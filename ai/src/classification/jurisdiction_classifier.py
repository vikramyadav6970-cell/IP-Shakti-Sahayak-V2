"""
ai/src/classification/jurisdiction_classifier.py

Deterministic and heuristic classifier for detecting active jurisdiction from user queries.
Identifies if an inquiry is Indian Law (INDIA), International Law (INTERNATIONAL), or crosses boundaries.
"""

import re
from typing import Tuple


INDIAN_LAW_MARKERS = [
    r"\bsection\s*3\s*\([a-z]\)",
    r"\bsection\s*3\s*\(p\)",
    r"\bsection\s*3\s*\(d\)",
    r"\bsection\s*3\s*\(e\)",
    r"\bpatents\s*act\s*(?:1970)?\b",
    r"\bbiological\s*diversity\s*act\b",
    r"\bbda\b",
    r"\bnba\b",
    r"\bsbb\b",
    r"\bayush\b",
    r"\bfssai\b",
    r"\bayurveda[-\s]*aahara\b",
    r"\bdrugs\s*(?:and|&)\s*cosmetics\b",
    r"\basu\b",
    r"\bindia(?:n)?\b",
    r"\btkdl\b",
    r"\bform\s*[i|ii|iii|iv]\b",
    r"\bip\s*india\b",
]

INTERNATIONAL_LAW_MARKERS = [
    r"\btrips\b",
    r"\bnagoya\s*protocol\b",
    r"\bconvention\s*on\s*biological\s*diversity\b",
    r"\bcbd\b",
    r"\bwipo\b",
    r"\bgratk\b",
    r"\buspto\b",
    r"\bepo\b",
    r"\bema\b",
    r"\bfda\b",
    r"\bukipo\b",
    r"\bmhra\b",
    r"\bjpo\b",
    r"\bpmda\b",
    r"\bcnipa\b",
    r"\bdpma\b",
    r"\binpi\b",
    r"\bip\s*australia\b",
    r"\bcipo\b",
    r"\bpatent\s*cooperation\s*treaty\b",
    r"\bpct\b",
    r"\bmadrid\s*system\b",
    r"\bbudapest\s*treaty\b",
    r"\bparis\s*convention\b",
    r"\bunited\s*states\b",
    r"\busa\b",
    r"\beuropean\s*union\b",
    r"\beurope\b",
    r"\beu\b",
    r"\bunited\s*kingdom\b",
    r"\buk\b",
    r"\bbrazil\b",
    r"\baustralia\b",
    r"\bgermany\b",
    r"\bfrance\b",
    r"\bcanada\b",
    r"\bjapan\b",
    r"\bchina\b",
    r"\bsouth\s*africa\b",
    r"\bexport\b",
    r"\bforeign\b",
    r"\babroad\b",
    r"\boverseas\b",
    r"\binternational\b",
]


class JurisdictionClassifier:
    """Classifies user queries into INDIA, INTERNATIONAL, or MIXED."""

    @staticmethod
    def classify(query: str, current_active: str = "INDIA") -> Tuple[str, bool, str]:
        """
        Returns:
            (detected_jurisdiction, is_out_of_scope, explanation)
        """
        q = query.lower()

        india_hits = [m for m in INDIAN_LAW_MARKERS if re.search(m, q)]
        intl_hits = [m for m in INTERNATIONAL_LAW_MARKERS if re.search(m, q)]

        if len(intl_hits) > len(india_hits) and len(intl_hits) > 0:
            detected = "INTERNATIONAL"
        elif len(india_hits) > len(intl_hits) and len(india_hits) > 0:
            detected = "INDIA"
        else:
            detected = current_active.upper()

        is_out_of_scope = False
        explanation = ""

        if current_active.upper() == "INDIA" and detected == "INTERNATIONAL" and len(intl_hits) >= 1:
            is_out_of_scope = True
            explanation = f"Query contains international legal markers ({', '.join(intl_hits[:2])}) while active jurisdiction is India."
        elif current_active.upper() == "INTERNATIONAL" and detected == "INDIA" and len(india_hits) >= 1:
            is_out_of_scope = True
            explanation = f"Query contains Indian statutory markers ({', '.join(india_hits[:2])}) while active jurisdiction is International."

        return detected, is_out_of_scope, explanation
