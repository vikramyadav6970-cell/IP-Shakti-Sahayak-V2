"""
backend/app/schemas/classification.py

Pydantic schemas for product formulation classification and IP protection mapping.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict


class FormulationCreate(BaseModel):
    name: str
    description: str
    ingredients: List[str]
    has_classical_text_reference: bool = False
    classical_text_name: Optional[str] = None
    is_strict_classical_recipe: bool = False
    has_novel_excipients_or_delivery: bool = False
    is_purified_standardized_fraction: bool = False
    is_food_or_dietary_supplement: bool = False
    has_synthetic_additives: bool = False
    target_market: str = "DOMESTIC"
    user_selected_category: Optional[str] = None


class ClassificationResponse(BaseModel):
    id: Optional[uuid.UUID] = None
    product_id: Optional[uuid.UUID] = None
    category: str
    category_name: str
    regulatory_pathway: str
    reasoning: Optional[str] = None
    rules_fired: List[str]
    is_reconciled: bool = False
    user_selected_category: Optional[str] = None
    ip_protection_map: Dict[str, Any]
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
