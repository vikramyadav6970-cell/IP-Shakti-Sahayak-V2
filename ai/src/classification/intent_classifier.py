"""
ai/src/classification/intent_classifier.py

Classifies user query intent to optimize retrieval routing and statutory response framing.
"""

import re
from typing import Dict, List, Optional, Tuple


INTENT_PATTERNS: Dict[str, List[str]] = {
    "PATENT": [
        r"\bpatent(?:able|ability|s)?\b",
        r"\bsection\s*3\s*\([a-z]\)",
        r"\bsection\s*3\s*\(p\)",
        r"\bsection\s*3\s*\(d\)",
        r"\bsection\s*3\s*\(e\)",
        r"\bnovelty\b",
        r"\binventive\s*step\b",
        r"\bprior\s*art\b",
        r"\btkdl\b",
        r"\bclaims?\b",
        r"\binvention\b",
        r"\btrade\s*secrets?\b",
        r"\bundisclosed\s*information\b",
        r"\bknow[-\s]*how\b",
        r"\bmonopoly\b",
    ],
    "ABS": [
        r"\babs\b",
        r"\babm(?:['’]s)?\b",
        r"\baccess\s*(?:and|&)?\s*benefit\s*sharing\b",
        r"\bbenefit\s*sharing\b",
        r"\bnba\b",
        r"\bnational\s*biodiversity\s*authority\b",
        r"\bstate\s*biodiversity\s*board\b",
        r"\bsbb\b",
        r"\bbiodiversity\b",
        r"\bbiological\s*(?:resources?|materials?|sources?|compliance)\b",
        r"\bform\s*i\b",
        r"\bform\s*iii\b",
        r"\bform\s*iv\b",
        r"\bpic\b",
        r"\bmat\b",
    ],
    "FORMULATION": [
        r"\bregulatory\s*(?:licensing|pathway|approval|compliance)\b",
        r"\blicensing\s*(?:pathway|requirements?|procedure)\b",
        r"\bmanufacturing\s*license\b",
        r"\bform\s*25-?d\b",
        r"\brule\s*153\b",
        r"\brule\s*158\b",
        r"\bdrugs?\s*(?:and|&)\s*cosmetics?\b",
        r"\bayush\s*license\b",
        r"\bclassical\s*(?:medicine|ayurvedic|ayurveda)\s*license\b",
        r"\bproprietary\s*(?:medicine|ayurvedic)\b",
        r"\bformulation\s*(?:license|licensing|standard|compliance|guidelines?)\b",
    ],
    "TRADEMARK": [
        r"\btrade\s*mark(?:s)?\b",
        r"\bbrand\s*(?:name|protection)?\b",
        r"\blogo\b",
        r"\bclass\s*5\b",
        r"\bclass\s*30\b",
        r"\bdeceptive\s*similarity\b",
        r"\bpassing\s*off\b",
        r"\bregistration\b",
    ],
    "FOOD_REGULATION": [
        r"\bayurveda[-\s]*aahara\b",
        r"\bfssai\b",
        r"\bfood\s*safety\b",
        r"\bdietary\s*supplement\b",
        r"\bnutraceutical\b",
        r"\bfood\s*vs\s*drug\b",
    ],
    "EXPORT": [
        r"\bexport(?:ing|s)?\b",
        r"\binternational\s*market\b",
        r"\bnagoya\b",
        r"\btrips\b",
        r"\bwipo\b",
        r"\buspto\b",
        r"\bfda\b",
        r"\bema\b",
        r"\bforeign\s*filing\b",
    ],
    "RESEARCH": [
        r"\bresearch\b",
        r"\bclinical\s*trial\b",
        r"\bstudy\b",
        r"\bjournal\b",
        r"\bscientific\s*validation\b",
    ],
}


AYUSH_DOMAIN_PATTERNS: List[str] = [
    # Traditional systems & frameworks
    r"\bayush\b",
    r"\bayurved(?:a|ic)?\b",
    r"\bsiddha\b",
    r"\bunani\b",
    r"\bsowa[-\s]*rigpa\b",
    r"\btraditional\s*(?:medicine|knowledge|formulation|practice|remedy)\b",
    r"\btkdl\b",
    r"\bherbal\b",
    r"\bbotanical\b",
    r"\bplant[-\s]*based\b",
    r"\bphytopharmaceutical\b",
    r"\bphyto[-\s]*\w+\b",
    # Classical preparations & Ayurvedic dosage forms
    r"\bbhasma\b",
    r"\btaila\b",
    r"\bghrita\b",
    r"\basava\b",
    r"\barishta\b",
    r"\bchurna\b",
    r"\bvati\b",
    r"\bgutika\b",
    r"\bkwatha\b",
    r"\brasayana\b",
    r"\blehyam\b",
    r"\bavaleha\b",
    r"\bkashayam\b",
    r"\bsvarasa\b",
    r"\blepa\b",
    r"\bmalhara\b",
    r"\barka\b",
    r"\bchyawanprash\b",
    # Botanical species & common medicinal herbs
    r"\bashwagandha\b",
    r"\bturmeric\b",
    r"\bcurcumin\b",
    r"\bgiloy\b",
    r"\bguduchi\b",
    r"\bneem\b",
    r"\btulsi\b",
    r"\btriphala\b",
    r"\bbrahmi\b",
    r"\bshatavari\b",
    r"\bamla\b",
    r"\bguggulu?\b",
    r"\bpippali\b",
    r"\bginger\b",
    r"\bgarlic\b",
    r"\bcardamom\b",
    r"\bclove\b",
    r"\bcinnamon\b",
    r"\baloe\s*vera\b",
    r"\bmoringa\b",
    r"\blicorice\b",
    r"\bmulethi\b",
    r"\bharitaki\b",
    r"\bbibhitaki\b",
    r"\barjuna\b",
    r"\bvasaka\b",
    r"\bshankhpushpi\b",
    r"\bmanjistha\b",
    r"\bkalmegh\b",
    r"\bbhringraj\b",
    r"\bsandalwood\b",
    r"\bchandana\b",
    r"\bkumkumadi\b",
    # Product, formulation, therapeutic context
    r"\bformulation\b",
    r"\bingredients?\b",
    r"\bproduct\s*(?:name|description|classification|details?)\b",
    r"\bclassify\s*(?:this|my)?\b",
    r"\bclassical\s*source\b",
    r"\btherapeutic\b",
    r"\bextract\b",
    r"\bdecoction\b",
    r"\btablets?\b",
    r"\bcapsules?\b",
    r"\bsyrups?\b",
    r"\bointment\b",
    r"\bhair\s*oil\b",
    r"\bskincare\b",
    r"\bimmunity\b",
    r"\bdigestion\b",
    r"\bdiabetes\b",
    r"\barthritis\b",
    # Conversational on-boarding / greeting
    r"\b(?:hello|hi|namaste|greetings|help|start|consultation)\b",
]


class IntentClassifier:
    """Classifies user inquiries into structured intent domains."""

    @staticmethod
    def is_in_domain(query: str, product_context: Optional[Dict] = None) -> Tuple[bool, float, str]:
        """
        Determines whether a user query falls within the Ayush/Traditional Medicine IP & regulatory domain.
        Returns (is_in_domain, confidence_score, matched_intent_or_reason).
        """
        q = query.lower().strip()
        if not q:
            return False, 0.0, "OUT_OF_SCOPE"

        # 1. If active product context exists (in-session dialogue), respect ongoing conversation
        if product_context:
            has_prod = bool(
                product_context.get("product_name")
                or product_context.get("ingredients")
                or product_context.get("description")
                or product_context.get("formulation")
                or product_context.get("state") in ["COLLECTING_PRODUCT_INFORMATION", "CLASSIFIED"]
            )
            if has_prod:
                return True, 0.85, "ACTIVE_CONTEXT"

        # 2. Check statutory intent patterns (PATENT, ABS, FORMULATION, TRADEMARK, etc.)
        matched_statutory: List[str] = []
        for intent, patterns in INTENT_PATTERNS.items():
            if any(re.search(p, q) for p in patterns):
                matched_statutory.append(intent)

        if matched_statutory:
            return True, 0.95, matched_statutory[0]

        # 3. Check Ayush domain / botanical / formulation keywords
        ayush_matches = sum(1 for p in AYUSH_DOMAIN_PATTERNS if re.search(p, q))
        if ayush_matches > 0:
            score = min(0.9, 0.4 + (ayush_matches * 0.15))
            return True, round(score, 2), "AYUSH_DOMAIN"

        # 4. Out of domain query (e.g. "what is a mobile", "how to repair car", general knowledge)
        return False, 0.0, "OUT_OF_SCOPE"

    @staticmethod
    def matches_intent(query: str, intent: str) -> bool:
        """Checks whether a query substring contains triggers for a specific intent."""
        patterns = INTENT_PATTERNS.get(intent, [])
        return any(re.search(p, query, re.IGNORECASE) for p in patterns)

    @staticmethod
    def classify(query: str, fallback_intent: Optional[str] = None) -> str:
        q = query.lower()
        scored_intents: Dict[str, int] = {}

        for intent, patterns in INTENT_PATTERNS.items():
            matches = sum(1 for p in patterns if re.search(p, q))
            if matches > 0:
                scored_intents[intent] = matches

        if not scored_intents:
            in_domain, _, reason = IntentClassifier.is_in_domain(query)
            if in_domain:
                return fallback_intent or "FORMULATION"
            return "OUT_OF_SCOPE"

        # Return intent with highest regex pattern matches
        sorted_intents = sorted(scored_intents.items(), key=lambda x: x[1], reverse=True)
        return sorted_intents[0][0]

    @staticmethod
    def classify_multi(query: str) -> List[Tuple[str, float]]:
        """
        Evaluates query against all statutory intent patterns and returns
        scored (intent, normalized_confidence) tuples.
        """
        q = query.lower()
        scored_intents: Dict[str, int] = {}
        total_matches = 0

        for intent, patterns in INTENT_PATTERNS.items():
            matches = sum(1 for p in patterns if re.search(p, q))
            if matches > 0:
                scored_intents[intent] = matches
                total_matches += matches

        if not scored_intents:
            in_domain, conf, _ = IntentClassifier.is_in_domain(query)
            if in_domain:
                return [("FORMULATION", conf)]
            return [("OUT_OF_SCOPE", 0.0)]

        results = []
        for intent, count in scored_intents.items():
            norm = round(count / max(1, total_matches), 2)
            results.append((intent, norm))

        return sorted(results, key=lambda x: x[1], reverse=True)
