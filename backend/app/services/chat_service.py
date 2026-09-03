import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure AI path is accessible
ai_path = str(Path(__file__).resolve().parent.parent.parent.parent / "ai")
if ai_path not in sys.path:
    sys.path.insert(0, ai_path)

from src.citations.citation_validator import CitationValidator
from src.classification.intent_classifier import IntentClassifier
from src.classification.jurisdiction_classifier import JurisdictionClassifier
from src.classification.product_classifier import CATEGORIES_REGISTRY, normalize_category_key, FormulationInput, ProductClassifier
from src.confidence.confidence_scorer import ConfidenceScorer
from src.embeddings.embedding_provider import get_embedding_provider
from src.embeddings.sparse_provider import BM25SparseProvider
from src.orchestration.decomposer import QueryDecomposer, AgentTask
from src.prompts.templates import (
    CONSULTATION_SYSTEM_PROMPT,
    build_user_prompt,
    build_multi_domain_user_prompt,
)
from src.reasoning.llm_provider import get_llm_provider
from src.retrieval.qdrant_manager import QdrantManager
from src.retrieval.retriever import HybridRetriever, DomainEvidenceSet

from app.config import settings
from app.models.entities import AuditLog, Citation, Conversation, Feedback, Message, User
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    CitationRead,
    ConversationRead,
    ConversationSummaryRead,
    FeedbackCreate,
    FeedbackRead,
    MessageRead,
    ProductClassificationMeta,
    ProductContextData,
)
from app.services.translation_service import translation_service

# Shared Singleton Instances for Fast In-Memory Reuse across requests
_SHARED_RETRIEVER: Optional[HybridRetriever] = None
_SHARED_QDRANT_MGR: Optional[QdrantManager] = None
_SHARED_SPARSE_PROV: Optional[BM25SparseProvider] = None


def get_shared_retriever() -> HybridRetriever:
    global _SHARED_RETRIEVER, _SHARED_QDRANT_MGR, _SHARED_SPARSE_PROV
    if _SHARED_RETRIEVER is None:
        dense_provider = get_embedding_provider()
        if _SHARED_SPARSE_PROV is None:
            _SHARED_SPARSE_PROV = BM25SparseProvider()
        if _SHARED_QDRANT_MGR is None:
            qdrant_in_memory = not bool(settings.QDRANT_URL and settings.QDRANT_API_KEY)
            _SHARED_QDRANT_MGR = QdrantManager(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                in_memory=qdrant_in_memory,
            )
        _SHARED_RETRIEVER = HybridRetriever(_SHARED_QDRANT_MGR, dense_provider, _SHARED_SPARSE_PROV)
    return _SHARED_RETRIEVER


class ChatService:
    """Consultation query orchestration & interactive product classification."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.chat_repo = ChatRepository(session)

        # Initialize shared AI providers (reusing singleton models & client connections)
        self.retriever = get_shared_retriever()
        self.dense_provider = self.retriever.dense_provider
        
        active_model = os.environ.get("LLM_MODEL") or settings.LLM_MODEL or "gemini-3.5-flash-lite"
        active_key = os.environ.get("GEMINI_API_KEY") or settings.GEMINI_API_KEY
        self.llm_provider = get_llm_provider(
            provider_name="gemini",
            model_name=active_model,
            api_key=active_key,
        )

    async def execute_chat(self, user: User, req: ChatRequest) -> ChatResponse:
        t_total_start = time.perf_counter()

        # 1. Resolve or prepare Conversation session
        conversation = None
        is_new_conv = False
        if req.conversation_id:
            conversation = await self.chat_repo.get_conversation(req.conversation_id)
            if not conversation or conversation.user_id != user.id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation session not found.")
        else:
            is_new_conv = True
            conversation = Conversation(
                id=uuid.uuid4(),
                user_id=user.id,
                title=req.question[:60] + ("..." if len(req.question) > 60 else ""),
                active_classification_id=req.active_classification_id,
                active_intent=req.active_intent,
            )

        # Update active classification context if provided in this turn
        if req.active_classification_id and not conversation.active_classification_id:
            conversation.active_classification_id = req.active_classification_id
        if req.active_intent and not conversation.active_intent:
            conversation.active_intent = req.active_intent

        # 2. Multilingual Processing & Guardrails
        t_trans_guard_start = time.perf_counter()
        input_lang = translation_service.normalize_language_code(req.language)
        if input_lang == "auto":
            detected_language = translation_service.detect_language(req.question)
        else:
            detected_language = input_lang

        is_indic_query = detected_language not in ["en-IN", "en"]
        core_question = req.question
        is_translated = False

        if is_indic_query:
            translated_q, trans_ok, trans_err = await translation_service.safe_translate_to_english(
                req.question, detected_language
            )
            if not trans_ok:
                if is_new_conv:
                    await self.chat_repo.create_conversation(conversation)

                user_msg = Message(
                    conversation_id=conversation.id,
                    role="user",
                    content=req.question,
                    jurisdiction=req.jurisdiction,
                )
                await self.chat_repo.add_message(user_msg)

                bot_msg = Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=(
                        "I am unable to translate your query at this moment. Please rephrase or try in English.\n\n"
                        "*(अनुवाद सेवा अस्थायी रूप से अनुपलब्ध है। कृपया अपना प्रश्न पुनः पूछें या अंग्रेजी में लिखें।)*"
                    ),
                    jurisdiction=req.jurisdiction,
                    requires_human_review=True,
                )
                bot_msg = await self.chat_repo.add_message(bot_msg)
                await self.session.commit()

                return ChatResponse(
                    conversation_id=conversation.id,
                    message_id=bot_msg.id,
                    content=bot_msg.content,
                    jurisdiction=req.jurisdiction,
                    requires_human_review=True,
                    citations=[],
                    detected_language=detected_language,
                    original_language=detected_language,
                    is_translated=False,
                )
            core_question = translated_q
            is_translated = True

        # Check Jurisdiction Guardrails (evaluated on English query)
        detected_jur, is_out_scope, out_explanation = JurisdictionClassifier.classify(
            core_question, current_active=req.jurisdiction
        )

        if is_out_scope:
            if is_new_conv:
                await self.chat_repo.create_conversation(conversation)

            user_msg = Message(
                conversation_id=conversation.id,
                role="user",
                content=req.question,
                jurisdiction=req.jurisdiction,
            )
            await self.chat_repo.add_message(user_msg)

            guardrail_text = f"Your inquiry appears to target {detected_jur} law rather than the active {req.jurisdiction} session. {out_explanation}"
            if is_indic_query:
                trans_guardrail, _, _ = await translation_service.safe_translate_from_english(
                    guardrail_text, detected_language
                )
                guardrail_text = trans_guardrail

            bot_msg = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=guardrail_text,
                jurisdiction=req.jurisdiction,
                confidence_score=0.95,
                confidence_label="HIGH",
                requires_human_review=False,
            )
            bot_msg = await self.chat_repo.add_message(bot_msg)
            await self.session.commit()

            return ChatResponse(
                conversation_id=conversation.id,
                message_id=bot_msg.id,
                content=bot_msg.content,
                jurisdiction=req.jurisdiction,
                confidence_score=0.95,
                confidence_label="HIGH",
                requires_human_review=False,
                citations=[],
                out_of_scope_detected=True,
                detected_jurisdiction=detected_jur,
                detected_language=detected_language,
                original_language="en-IN" if is_indic_query else detected_language,
                is_translated=is_translated,
            )

        t_trans_guard_ms = (time.perf_counter() - t_trans_guard_start) * 1000

        # 3. Parse existing prior product context
        # 3. Resolve Intent & Multi-Agent Decomposition
        t_context_start = time.perf_counter()
        prev_context_data: Dict[str, Any] = {}
        if req.active_product_context:
            try:
                prev_context_data = json.loads(req.active_product_context)
            except Exception:
                pass
        elif conversation.product_context_json:
            prev_context_data = conversation.product_context_json

        explicit_intent = req.active_intent.value if req.active_intent else None
        agent_tasks: List[AgentTask] = QueryDecomposer.decompose(
            query=core_question,
            jurisdiction=req.jurisdiction,
            explicit_intent=explicit_intent,
        )
        is_multi_agent = len(agent_tasks) > 1
        t_context_ms = (time.perf_counter() - t_context_start) * 1000

        # 4. Scoped Hybrid Retrieval (Parallel multi-domain or single-pass fast path)
        t_retrieval_start = time.perf_counter()
        evidence_hits: List[RetrievedEvidence] = []
        domain_evidence_map: Dict[str, Any] = {}

        if not is_multi_agent:
            single_task = agent_tasks[0]
            intent = single_task.intent
            t_single_start = time.perf_counter()
            evidence_hits = await asyncio.to_thread(
                self.retriever.retrieve,
                query=single_task.sub_question,
                jurisdiction=single_task.jurisdiction,
                intent=single_task.intent,
                top_k=4,
            )
            t_single_ms = (time.perf_counter() - t_single_start) * 1000
            evidence_dicts = [e.to_dict() for e in evidence_hits]
            system_prompt = CONSULTATION_SYSTEM_PROMPT
            user_prompt = build_user_prompt(
                question=core_question,
                jurisdiction=req.jurisdiction,
                intent=intent,
                evidence_items=evidence_dicts,
                classification_category=prev_context_data.get("category"),
                product_context=req.active_product_context,
            )

            t_retrieval_ms = (time.perf_counter() - t_retrieval_start) * 1000

            # Terminal Logging: Single-Agent retrieval results
            print("\n" + "=" * 80)
            print(" [VECTOR RETRIEVAL - SINGLE-AGENT]")
            print(f" Query: '{core_question}'")
            print(f" Jurisdiction: {req.jurisdiction} | Overall Retrieval Time: {t_retrieval_ms:.1f}ms | Total Chunks: {len(evidence_hits)}")
            print("-" * 80)
            print(f" [Agent: {single_task.agent_scope}] (Intent: {single_task.intent}) -> Retrieved {len(evidence_hits)} chunks in {t_single_ms:.1f}ms:")
            if evidence_hits:
                for idx, ev in enumerate(evidence_hits, 1):
                    clean_title = ev.doc_title or "Unknown Document"
                    clean_sec = ev.section_ref or "General Provision"
                    clean_snippet = ev.content.replace('\n', ' ')[:180].encode('ascii', errors='replace').decode('ascii')
                    print(f"   [{idx}] Score: {ev.score:.4f} | Doc: {clean_title} | Sec: {clean_sec} | Type: {ev.document_type}")
                    print(f"       Snippet: {clean_snippet}...")
            else:
                print("   (No matching statutory chunks retrieved for this filter)")
            print("=" * 80 + "\n")
        else:
            # Multi-Agent Orchestration: parallel domain-scoped retrieval with individual timers
            async def _retrieve_scoped(task: AgentTask):
                t_sub_start = time.perf_counter()
                d_set = await asyncio.to_thread(self.retriever.retrieve_for_task, task, 3)
                t_sub_ms = (time.perf_counter() - t_sub_start) * 1000
                return d_set, t_sub_ms

            scoped_results = await asyncio.gather(*[_retrieve_scoped(task) for task in agent_tasks])

            for d_set, sub_ms in scoped_results:
                domain_evidence_map[d_set.agent_scope] = {
                    "agent_scope": d_set.agent_scope,
                    "intent": d_set.intent,
                    "sub_question": d_set.sub_question,
                    "evidence": [e.to_dict() for e in d_set.evidence],
                    "hits_found": d_set.hits_found,
                    "duration_ms": sub_ms,
                }
                evidence_hits.extend(d_set.evidence)

            intent = "+".join([t.intent for t in agent_tasks])
            system_prompt = CONSULTATION_SYSTEM_PROMPT
            user_prompt = build_multi_domain_user_prompt(
                question=core_question,
                jurisdiction=req.jurisdiction,
                domain_evidence_map=domain_evidence_map,
                classification_category=prev_context_data.get("category"),
                product_context=req.active_product_context,
            )

            t_retrieval_ms = (time.perf_counter() - t_retrieval_start) * 1000

            # Terminal Logging: Multi-Agent domain-scoped retrieval breakdown
            print("\n" + "=" * 80)
            print(f" [VECTOR RETRIEVAL ORCHESTRATION] (MULTI-AGENT: {len(agent_tasks)} AGENTS)")
            print(f" Query: '{core_question}'")
            print(f" Jurisdiction: {req.jurisdiction} | Overall Retrieval Time: {t_retrieval_ms:.1f}ms | Total Chunks: {len(evidence_hits)}")
            print("-" * 80)

            for d_set, sub_ms in scoped_results:
                print(f" [Agent: {d_set.agent_scope}] (Intent: {d_set.intent}) -> Retrieved {len(d_set.evidence)} chunks in {sub_ms:.1f}ms:")
                print(f"   Sub-Query: '{d_set.sub_question}'")
                if d_set.evidence:
                    for idx, ev in enumerate(d_set.evidence, 1):
                        clean_title = ev.doc_title or "Unknown Document"
                        clean_sec = ev.section_ref or "General Provision"
                        clean_snippet = ev.content.replace('\n', ' ')[:180].encode('ascii', errors='replace').decode('ascii')
                        print(f"   [{idx}] Score: {ev.score:.4f} | Doc: {clean_title} | Sec: {clean_sec} | Type: {ev.document_type}")
                        print(f"       Snippet: {clean_snippet}...")
                else:
                    print("   (No matching domain chunks retrieved)")
                print()
            print("=" * 80 + "\n")

        if is_indic_query:
            user_prompt += (
                "\n\nCRITICAL CONCISENESS REQUIREMENT: The user is consulting in an Indian language. "
                "Your advisory response (excluding the [[PRODUCT_CONTEXT:...]] tag) MUST BE CONCISE, CRISP, "
                "AND STRICTLY UNDER 800 CHARACTERS (under 120 words). Provide direct legal conclusions, specific Section references "
                "(e.g., Section 3(p), Section 3(e), Form 25-D), and brief bullet points so that the output translates cleanly within character limits."
            )

        # 5. Generate answer via LLM Provider
        t_llm_start = time.perf_counter()
        is_generation_error = False
        try:
            answer_text = await asyncio.to_thread(self.llm_provider.generate, system_prompt, user_prompt)
        except Exception as err:
            print(f"\n[LLM Generation Notice/Error]: {err}")
            is_generation_error = True
            answer_text = "I am unable to answer that at this moment. Please try again in a few moments."
        t_llm_ms = (time.perf_counter() - t_llm_start) * 1000

        # 6. Extract embedded [[PRODUCT_CONTEXT:{...}]] tag
        t_extract_start = time.perf_counter()
        product_context_data: Optional[ProductContextData] = None
        product_classification_meta: Optional[ProductClassificationMeta] = None

        context_match = re.search(r"\[\[PRODUCT_CONTEXT:\s*(?:```json)?\s*(\{[\s\S]*?\})\s*(?:```)?\s*\]\]", answer_text, re.DOTALL)
        if context_match:
            try:
                raw_json = context_match.group(1).strip()
                parsed = json.loads(raw_json)
                # Merge previous context with new fields
                merged = {**prev_context_data, **parsed}

                cat_raw = merged.get("category")
                cat_key = normalize_category_key(cat_raw) if cat_raw else None
                cat_registry_info = CATEGORIES_REGISTRY.get(cat_key, CATEGORIES_REGISTRY.get("PROPRIETARY_MEDICINE"))

                is_classified = (
                    merged.get("state") == "CLASSIFIED"
                    or (cat_key is not None and cat_key != "UNCLEAR")
                )
                state_str = "CLASSIFIED" if is_classified else (merged.get("state") or "COLLECTING_PRODUCT_INFORMATION")

                product_context_data = ProductContextData(
                    product_name=merged.get("product_name"),
                    description=merged.get("description"),
                    formulation=merged.get("formulation"),
                    ingredients=merged.get("ingredients") if isinstance(merged.get("ingredients"), list) else ([merged["ingredients"]] if merged.get("ingredients") else None),
                    dosage_form=merged.get("dosage_form"),
                    intended_use=merged.get("intended_use"),
                    therapeutic_claims=merged.get("therapeutic_claims"),
                    classical_source=merged.get("classical_source"),
                    other_relevant_info=merged.get("other_relevant_info"),
                    state=state_str,
                    category=cat_registry_info["name"] if cat_key else cat_raw,
                    category_name=cat_registry_info["name"] if cat_key else cat_raw,
                    classification_reason=merged.get("classification_reason") or (cat_registry_info["short_desc"] if cat_key else None),
                    regulatory_pathway=merged.get("regulatory_pathway") or (cat_registry_info["regulatory_pathway"] if cat_key else None),
                    statutory_authority=merged.get("statutory_authority") or (cat_registry_info["statutory_authority"] if cat_key else None),
                    patent_eligibility=merged.get("patent_eligibility") or (cat_registry_info["patent_eligibility"] if cat_key else None),
                    patent_reasoning=cat_registry_info["patent_reasoning"] if cat_key else None,
                    abs_requirement=cat_registry_info["abs_requirement"] if cat_key else None,
                )

                if is_classified and cat_key:
                    product_classification_meta = ProductClassificationMeta(
                        category=cat_key,
                        category_name=cat_registry_info["name"],
                        product_name=merged.get("product_name") or "Ayurvedic Product",
                        regulatory_pathway=cat_registry_info["regulatory_pathway"],
                        statutory_authority=cat_registry_info["statutory_authority"],
                        reasoning=merged.get("classification_reason") or cat_registry_info["short_desc"],
                        patent_eligibility=cat_registry_info["patent_eligibility"],
                        patent_reasoning=cat_registry_info["patent_reasoning"],
                        abs_requirement=cat_registry_info["abs_requirement"],
                        confidence=0.92,
                    )

                # Clean the response text for user display
                answer_text = answer_text.replace(context_match.group(0), "").strip()
            except Exception as ex:
                print(f"[Product Context Extraction Notice]: {ex}")

        # Text-based Classification Fallback:
        # Detect explicit classification announcements in text (e.g. "classified as: **Ayurveda-Aahar / Nutraceutical**")
        text_lower = answer_text.lower()
        if (not product_classification_meta or (product_context_data and product_context_data.state != "CLASSIFIED")) and (
            "classified as" in text_lower or "product is classified" in text_lower or "classification:" in text_lower or "category:" in text_lower
        ):
            detected_category_key = None
            if "ayurveda-aahar" in text_lower or "ayurveda aahar" in text_lower or "nutraceutical" in text_lower:
                detected_category_key = "AYURVEDA_AAHARA"
            elif "patent-or-proprietary" in text_lower or "patent or proprietary" in text_lower or "proprietary medicine" in text_lower:
                detected_category_key = "PROPRIETARY_MEDICINE"
            elif "phytopharmaceutical" in text_lower:
                detected_category_key = "PHYTOPHARMACEUTICAL"
            elif "new or non-classical" in text_lower or "new drug" in text_lower or "non-classical drug" in text_lower:
                detected_category_key = "NEW_DRUG"
            elif "cosmetic" in text_lower and not ("classical" in text_lower and "generic" in text_lower):
                detected_category_key = "COSMETIC"
            elif "classical" in text_lower and ("generic" in text_lower or "medicine" in text_lower or "monograph" in text_lower or "first-schedule" in text_lower or "first schedule" in text_lower):
                detected_category_key = "CLASSICAL_MEDICINE"

            if detected_category_key:
                cat_info = CATEGORIES_REGISTRY[detected_category_key]
                reason_match = re.search(r"(?:\*\*Reason:\*\*|Reason:)\s*(.+?)(?:\n\n|\Z)", answer_text, re.DOTALL | re.IGNORECASE)
                reason_text = reason_match.group(1).strip() if reason_match else cat_info["short_desc"]

                base_dict = product_context_data.to_dict() if product_context_data else prev_context_data
                product_context_data = ProductContextData(
                    product_name=base_dict.get("product_name") or "Ayurvedic Product",
                    description=base_dict.get("description") or req.question[:120],
                    formulation=base_dict.get("formulation"),
                    ingredients=base_dict.get("ingredients"),
                    dosage_form=base_dict.get("dosage_form"),
                    intended_use=base_dict.get("intended_use"),
                    therapeutic_claims=base_dict.get("therapeutic_claims"),
                    classical_source=base_dict.get("classical_source"),
                    other_relevant_info=base_dict.get("other_relevant_info"),
                    state="CLASSIFIED",
                    category=cat_info["name"],
                    category_name=cat_info["name"],
                    classification_reason=reason_text,
                    regulatory_pathway=cat_info["regulatory_pathway"],
                    statutory_authority=cat_info["statutory_authority"],
                    patent_eligibility=cat_info["patent_eligibility"],
                    patent_reasoning=cat_info["patent_reasoning"],
                    abs_requirement=cat_info["abs_requirement"],
                )
                product_classification_meta = ProductClassificationMeta(
                    category=detected_category_key,
                    category_name=cat_info["name"],
                    product_name=product_context_data.product_name or "Ayurvedic Product",
                    regulatory_pathway=cat_info["regulatory_pathway"],
                    statutory_authority=cat_info["statutory_authority"],
                    reasoning=reason_text,
                    patent_eligibility=cat_info["patent_eligibility"],
                    patent_reasoning=cat_info["patent_reasoning"],
                    abs_requirement=cat_info["abs_requirement"],
                    confidence=0.92,
                )

        # 7. Persist conversation, user message, bot message, and citations
        if is_new_conv:
            await self.chat_repo.create_conversation(conversation)

        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=req.question,
            jurisdiction=req.jurisdiction,
        )
        await self.chat_repo.add_message(user_msg)

        # 7. Validate Citations and Compute Dynamic Multi-Factor Confidence Score
        # 7. Validate Citations and Compute Dynamic Multi-Factor Confidence Score
        validated_citations, citation_ratio = CitationValidator.validate_citations(
            response_text=answer_text,
            retrieved_evidence=evidence_hits,
            jurisdiction=req.jurisdiction,
        )

        domain_confidence_dict: Optional[Dict[str, Any]] = None
        if is_multi_agent:
            multi_assessment = ConfidenceScorer.calculate_multi_domain_confidence(
                response_text=answer_text,
                domain_evidence_map=domain_evidence_map,
                validated_citations=validated_citations,
            )
            confidence_score = multi_assessment.overall_composite_score
            confidence_label = multi_assessment.overall_confidence_label
            requires_human_review = multi_assessment.requires_human_review
            domain_confidence_dict = multi_assessment.domain_confidence
        else:
            confidence_assessment = ConfidenceScorer.calculate_confidence(
                response_text=answer_text,
                evidence_hits=evidence_hits,
                validated_citations=validated_citations,
                citation_ratio=citation_ratio,
            )
            confidence_score = confidence_assessment.composite_score
            confidence_label = confidence_assessment.confidence_label
            requires_human_review = confidence_assessment.requires_human_review

        # 8. Persist Citations ONLY if actual evidence was retrieved from RAG
        persisted_citations: List[CitationRead] = []
        has_legal_intent = bool(
            req.active_intent
            or req.active_classification_id
            or any(k in req.question.lower() for k in ["patent", "section 3", "abs", "nba", "fssai", "license", "trips", "statute"])
        )
        is_diagnostic_interview = bool(
            product_context_data
            and product_context_data.state == "COLLECTING_PRODUCT_INFORMATION"
            and not has_legal_intent
        )

        # Citations are strictly attached ONLY when real RAG retrieval chunks are present
        if not is_generation_error and evidence_hits and not is_diagnostic_interview:
            for hit in evidence_hits:
                cit = Citation(
                    message_id=uuid.uuid4(),  # temporary, will assign to bot_msg
                    document_title=hit.doc_title,
                    section_ref=hit.section_ref or "General Provision",
                    source_url=hit.source_url,
                    jurisdiction=hit.jurisdiction,
                    document_type=hit.document_type,
                )
                persisted_citations.append(
                    CitationRead(
                        id=cit.id,
                        document_title=hit.doc_title,
                        section_ref=hit.section_ref or "General Provision",
                        source_url=hit.source_url,
                        jurisdiction=hit.jurisdiction,
                        document_type=hit.document_type,
                        verification_status=hit.verification_status,
                    )
                )

        # 9. Clean Product Context tag & Translate Output to Indic Language if required
        clean_answer_text = re.sub(
            r"\[\[PRODUCT_CONTEXT:\s*(?:```json)?\s*\{[\s\S]*?\}\s*(?:```)?\s*\]\]", "", answer_text, flags=re.DOTALL
        ).strip()

        final_answer_text = clean_answer_text
        if is_indic_query and not is_generation_error:
            translated_ans, trans_out_ok, trans_out_err = await translation_service.safe_translate_from_english(
                clean_answer_text, detected_language
            )
            if trans_out_ok:
                final_answer_text = translated_ans
                is_translated = True
            else:
                is_translated = False
                final_answer_text = (
                    f"{clean_answer_text}\n\n"
                    f"*(Note: Translation to your language was temporarily unavailable; showing advisory in English.)*"
                )

        t_extract_ms = (time.perf_counter() - t_extract_start) * 1000

        # 10. Database persistence & DPDP audit logging
        t_db_start = time.perf_counter()

        if is_generation_error:
            confidence_score = 0.0
            confidence_label = "LOW"
            requires_human_review = True
        elif len(persisted_citations) > 0:
            confidence_score = confidence_assessment.composite_score
            confidence_label = confidence_assessment.confidence_label
            requires_human_review = confidence_assessment.requires_human_review
        else:
            # For pure product intake, questions, or conversational turns without RAG evidence
            confidence_score = None
            confidence_label = None
            requires_human_review = False

        bot_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=final_answer_text,
            jurisdiction=req.jurisdiction,
            confidence_score=confidence_score,
            confidence_label=confidence_label,
            requires_human_review=requires_human_review,
        )
        bot_msg = await self.chat_repo.add_message(bot_msg)

        # Link citations to persisted bot_msg id
        for cit_read in persisted_citations:
            db_cit = Citation(
                id=cit_read.id,
                message_id=bot_msg.id,
                document_title=cit_read.document_title,
                section_ref=cit_read.section_ref,
                source_url=cit_read.source_url,
                jurisdiction=cit_read.jurisdiction,
                document_type=cit_read.document_type,
            )
            await self.chat_repo.add_citation(db_cit)

        # Persist structured product context on conversation record
        if product_context_data:
            conversation.product_context_json = product_context_data.model_dump()
            conversation.classification_state = product_context_data.state
            if product_context_data.product_name:
                conversation.title = product_context_data.product_name

        # Audit logging (DPDP compliance)
        audit = AuditLog(
            user_id=user.id,
            action="CHAT_QUERY",
            resource_type="Conversation",
            resource_id=str(conversation.id),
            metadata_json={
                "jurisdiction": req.jurisdiction,
                "intent": intent,
                "multi_agent": is_multi_agent,
                "confidence": confidence_score,
                "domain_confidence": domain_confidence_dict,
                "citations_count": len(persisted_citations),
                "classification_state": product_context_data.state if product_context_data else "PENDING",
                "classified_category": product_classification_meta.category if product_classification_meta else None,
                "detected_language": detected_language,
                "is_translated": is_translated,
            },
        )
        await self.chat_repo.add_audit_log(audit)

        await self.session.commit()
        t_db_ms = (time.perf_counter() - t_db_start) * 1000

        t_total_sec = time.perf_counter() - t_total_start

        # Terminal Performance Breakdown
        print("\n" + "=" * 78)
        print(" [AI PIPELINE STEP-BY-STEP LATENCY BREAKDOWN]")
        print(f"   * [1/6] Multilingual & Guardrails   : {t_trans_guard_ms:6.1f} ms")
        print(f"   * [2/6] Intent & Context Resolution : {t_context_ms:6.1f} ms")
        print(f"   * [3/6] Hybrid Parallel Retrieval   : {t_retrieval_ms:6.1f} ms ({len(evidence_hits)} hits from Qdrant)")
        print(f"   * [4/6] Gemini LLM Reasoning (AI)  : {t_llm_ms:6.1f} ms")
        print(f"   * [5/6] Context & Citation Parsing  : {t_extract_ms:6.1f} ms")
        print(f"   * [6/6] Database Commit & Audit Log : {t_db_ms:6.1f} ms")
        print(" " + "-" * 76)
        print(f" >>> TOTAL TURN-AROUND LATENCY       : {t_total_sec:6.3f} s")
        print("=" * 78 + "\n")

        return ChatResponse(
            conversation_id=conversation.id,
            message_id=bot_msg.id,
            content=final_answer_text,
            jurisdiction=req.jurisdiction,
            confidence_score=confidence_score,
            confidence_label=confidence_label,
            requires_human_review=bot_msg.requires_human_review,
            citations=persisted_citations,
            out_of_scope_detected=False,
            detected_language=detected_language,
            original_language="en-IN" if is_indic_query else detected_language,
            is_translated=is_translated,
            product_classification=product_classification_meta,
            product_context=product_context_data,
            domain_confidence=domain_confidence_dict,
        )

    async def list_user_conversations(self, user: User) -> List[ConversationSummaryRead]:
        convs = await self.chat_repo.list_conversations(user.id)
        summaries = []
        for c in convs:
            try:
                p_json = c.product_context_json or {}

                # Determine product name
                prod_name = (
                    p_json.get("product_name")
                    or (c.title if c.title and not c.title.startswith("Please provide") else None)
                    or (p_json.get("description")[:40] + "..." if p_json.get("description") else None)
                    or "Ayurvedic Formulation"
                )

                # Determine category details
                cat_raw = p_json.get("category")
                cat_name = p_json.get("category_name")
                regulatory_pathway = p_json.get("regulatory_pathway")
                patent_eligibility = p_json.get("patent_eligibility")

                if cat_raw and not cat_name:
                    cat_key = normalize_category_key(cat_raw)
                    cat_info = CATEGORIES_REGISTRY.get(cat_key)
                    if cat_info:
                        cat_name = cat_info["name"]
                        if not regulatory_pathway:
                            regulatory_pathway = cat_info["regulatory_pathway"]
                        if not patent_eligibility:
                            patent_eligibility = cat_info["patent_eligibility"]

                msg_count = len(c.messages) if ("messages" in c.__dict__ and c.messages) else 0

                summaries.append(
                    ConversationSummaryRead(
                        id=c.id,
                        title=prod_name,
                        active_classification_id=c.active_classification_id,
                        active_intent=c.active_intent,
                        product_name=prod_name,
                        category=cat_raw,
                        category_name=cat_name,
                        dosage_form=p_json.get("dosage_form"),
                        ingredients=p_json.get("ingredients") or [],
                        patent_eligibility=patent_eligibility,
                        regulatory_pathway=regulatory_pathway,
                        classification_state=c.classification_state or p_json.get("state") or "COLLECTING_PRODUCT_INFORMATION",
                        message_count=msg_count,
                        created_at=c.created_at,
                        updated_at=c.updated_at,
                    )
                )
            except Exception as ex:
                print(f"[Conversation Summary Format Notice]: {ex}")
                summaries.append(
                    ConversationSummaryRead(
                        id=c.id,
                        title=c.title or "Ayurvedic Consultation",
                        active_classification_id=c.active_classification_id,
                        active_intent=c.active_intent,
                        classification_state=c.classification_state or "COLLECTING_PRODUCT_INFORMATION",
                        message_count=0,
                        created_at=c.created_at,
                        updated_at=c.updated_at,
                    )
                )
        return summaries

    async def get_conversation_details(self, user: User, conv_id: uuid.UUID) -> ConversationRead:
        conv = await self.chat_repo.get_conversation(conv_id)
        if not conv or conv.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

        # Build product_context and classification meta from stored JSON if present
        p_data = None
        p_meta = None
        if conv.product_context_json:
            try:
                p_data = ProductContextData(**conv.product_context_json)
                if p_data.category:
                    cat_key = normalize_category_key(p_data.category)
                    cat_info = CATEGORIES_REGISTRY.get(cat_key, CATEGORIES_REGISTRY.get("PROPRIETARY_MEDICINE"))
                    p_meta = ProductClassificationMeta(
                        category=cat_key or "PROPRIETARY_MEDICINE",
                        category_name=cat_info["name"],
                        product_name=p_data.product_name or conv.title or "Ayurvedic Product",
                        regulatory_pathway=cat_info["regulatory_pathway"],
                        statutory_authority=cat_info["statutory_authority"],
                        reasoning=p_data.classification_reason or cat_info["short_desc"],
                        patent_eligibility=cat_info["patent_eligibility"],
                        patent_reasoning=cat_info["patent_reasoning"],
                        abs_requirement=cat_info["abs_requirement"],
                        confidence=0.96,
                    )
            except Exception as ex:
                print(f"[Conversation Detail Load Notice]: {ex}")

        # Map messages with citations
        msg_reads = []
        raw_messages = conv.messages if ("messages" in conv.__dict__ and conv.messages) else []
        for m in raw_messages:
            raw_citations = m.citations if ("citations" in m.__dict__ and m.citations) else []
            cit_reads = [
                CitationRead(
                    id=c.id,
                    document_title=c.document_title,
                    section_ref=c.section_ref,
                    source_url=c.source_url,
                    jurisdiction=c.jurisdiction,
                    document_type=c.document_type,
                )
                for c in raw_citations
            ]
            msg_reads.append(
                MessageRead(
                    id=m.id,
                    conversation_id=m.conversation_id,
                    role=m.role,
                    content=m.content,
                    jurisdiction=m.jurisdiction,
                    confidence_score=m.confidence_score,
                    confidence_label=m.confidence_label,
                    requires_human_review=m.requires_human_review,
                    classification=m.classification,
                    created_at=m.created_at,
                    citations=cit_reads,
                )
            )

        return ConversationRead(
            id=conv.id,
            user_id=conv.user_id,
            title=conv.title or (p_data.product_name if p_data else "Ayurvedic Consultation"),
            active_classification_id=conv.active_classification_id,
            active_intent=conv.active_intent,
            product_context=p_data,
            product_classification=p_meta,
            classification_state=conv.classification_state or (p_data.state if p_data else "COLLECTING_PRODUCT_INFORMATION"),
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            messages=msg_reads,
        )

    async def delete_user_conversation(self, user: User, conv_id: uuid.UUID) -> bool:
        success = await self.chat_repo.delete_conversation(conv_id, user.id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
        await self.session.commit()
        return True

    async def add_message_feedback(self, user: User, message_id: uuid.UUID, data: FeedbackCreate) -> FeedbackRead:
        fb = Feedback(
            message_id=message_id,
            user_id=user.id,
            rating=data.rating,
            comment=data.comment,
        )
        fb = await self.chat_repo.add_feedback(fb)
        await self.session.commit()
        return FeedbackRead.model_validate(fb)
