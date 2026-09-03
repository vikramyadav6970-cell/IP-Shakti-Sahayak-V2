"""
ai/src/classification/intent_classifier.py

Classifies user query intent to optimize retrieval routing and statutory response framing.
"""

import re
from typing import Dict, List, Optional


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


class IntentClassifier:
    """Classifies user inquiries into structured intent domains."""

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
            return fallback_intent or "PATENT"

        # Return intent with highest regex pattern matches
        sorted_intents = sorted(scored_intents.items(), key=lambda x: x[1], reverse=True)
        return sorted_intents[0][0]

    @staticmethod
    def classify_multi(query: str) -> List[tuple[str, float]]:
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
            return [("PATENT", 1.0)]

        results = []
        for intent, count in scored_intents.items():
            norm = round(count / max(1, total_matches), 2)
            results.append((intent, norm))

        return sorted(results, key=lambda x: x[1], reverse=True)
