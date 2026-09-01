"""
backend/app/api/v1/ip.py

Comprehensive IP Assessment API endpoint.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import IPAssessment, User
from app.schemas.ip_abs import IPAssessmentRequest, IPAssessmentResponse
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/ip", tags=["IP Assessment"])


@router.post(
    "",
    response_model=IPAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate comprehensive multi-right IP assessment roadmap",
)
async def assess_ip(
    req: IPAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates Patent, Trademark, Geographical Indication, and ABS rights for the product.
    """
    cat = req.category.upper()
    has_novel = req.has_novel_tech

    if cat == "CLASSICAL_MEDICINE":
        patent_elig = "EXCLUDED"
        patent_reason = (
            "Statutorily excluded under Section 3(p) of the Patents Act, 1970 as traditional knowledge. "
            "Classical recipes found in First Schedule texts cannot be monopolized under patent law."
        )
        tm_rec = "Register distinctive wordmark/logo under Nice Class 5. Classical names (e.g. 'Triphala Churna') cannot be registered as trademarks."
        abs_req = "Indian entities require SBB prior intimation (exempt fee under 2023 amendment for AYUSH practitioners). Foreign entities require NBA Form I."
        gi_rec = "Check if raw herbs originate from GI-designated regions (e.g., Kashmir Saffron, Malabar Pepper, Edayur Chilli)."
        roadmap = [
            "1. Focus IP budget on Brand Trademark registration in Nice Class 5.",
            "2. Ensure SBB prior intimation for commercial manufacturing.",
            "3. Obtain Form 25-D AYUSH Manufacturing License.",
            "4. Do not file patent for classical formulation.",
        ]
    elif cat == "PHYTOPHARMACEUTICAL":
        patent_elig = "HIGH"
        patent_reason = (
            "Patentable if the purified fraction is characterized with minimum 4 bioactive markers, "
            "demonstrates novelty over crude extracts, and exhibits an inventive therapeutic extraction process."
        )
        tm_rec = "Register trademark for active fraction brand name and formulation trademark in Class 5."
        abs_req = "Mandatory NBA Form III approval prior to patent grant (Section 6) and Form I for access."
        gi_rec = "GI tag relevance for authentic species sourcing validation."
        roadmap = [
            "1. File NBA Form III application before patent grant.",
            "2. File Patent Application claiming standardized fraction and extraction process.",
            "3. Obtain CDSCO Form CT-20 phytopharmaceutical clinical trial approval.",
            "4. File Class 5 Trademark for brand name.",
        ]
    else:  # PROPRIETARY_MEDICINE / AYURVEDA_AAHARA
        patent_elig = "CONDITIONAL" if has_novel else "EXCLUDED"
        patent_reason = (
            "Patentable only if comparative synergistic efficacy data proves bio-enhancement beyond mere additive effect (Section 3(e) & 3(p))."
            if has_novel
            else "Excluded under Section 3(e) and 3(p) as a mere admixture resulting only in the aggregation of known herbal properties."
        )
        tm_rec = "Register proprietary brand name and distinctive packaging under Nice Class 5 (ASU Medicine) or Class 30 (Ayurveda Aahara)."
        abs_req = "SBB intimation for Indian commercial manufacturers; NBA Form I for entities with foreign equity."
        gi_rec = "Applicable if claiming specific geographical variety of herbal ingredients."
        roadmap = [
            "1. Conduct synergy testing if seeking patent protection.",
            "2. File Trademark in Class 5 or Class 30.",
            "3. Submit SBB prior intimation.",
            "4. Obtain AYUSH Form 25-D or FSSAI Ayurveda-Aahara license.",
        ]

    record = IPAssessment(
        product_id=req.product_id,
        ip_type="MULTI_RIGHT_ASSESSMENT",
        relevance_label=patent_elig,
        reasoning=patent_reason,
        legal_provisions=[{"trademark": tm_rec, "abs": abs_req, "gi": gi_rec, "roadmap": roadmap}],
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return IPAssessmentResponse(
        id=record.id,
        product_id=req.product_id,
        product_name=req.product_name,
        category=req.category,
        patent_eligibility=patent_elig,
        patent_reasoning=patent_reason,
        trademark_recommendation=tm_rec,
        abs_requirement=abs_req,
        gi_relevance=gi_rec,
        actionable_roadmap=roadmap,
        created_at=record.created_at,
    )
