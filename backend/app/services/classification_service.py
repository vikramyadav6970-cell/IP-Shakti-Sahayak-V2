"""
backend/app/services/classification_service.py

Service layer executing deterministic product classification rules and persisting records.
"""

from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

# Import AI rules engine
import sys
from pathlib import Path

# Ensure AI path is accessible
ai_path = str(Path(__file__).resolve().parent.parent.parent.parent / "ai")
if ai_path not in sys.path:
    sys.path.insert(0, ai_path)

from src.classification.product_classifier import FormulationInput, ProductClassifier
from app.models.entities import Classification, Product, User
from app.schemas.classification import ClassificationResponse, FormulationCreate


class ClassificationService:
    """Orchestrates product classification and persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def classify_product(
        self,
        form: FormulationCreate,
        current_user: Optional[User] = None,
    ) -> ClassificationResponse:
        # Convert Pydantic model to FormulationInput
        f_input = FormulationInput(
            name=form.name,
            description=form.description,
            ingredients=form.ingredients,
            has_classical_text_reference=form.has_classical_text_reference,
            classical_text_name=form.classical_text_name,
            is_strict_classical_recipe=form.is_strict_classical_recipe,
            has_novel_excipients_or_delivery=form.has_novel_excipients_or_delivery,
            is_purified_standardized_fraction=form.is_purified_standardized_fraction,
            is_food_or_dietary_supplement=form.is_food_or_dietary_supplement,
            has_synthetic_additives=form.has_synthetic_additives,
            target_market=form.target_market,
            user_selected_category=form.user_selected_category,
        )

        engine_result = ProductClassifier.classify(f_input)

        product_id = None
        classification_id = None

        # If authenticated, persist Product and Classification
        if current_user:
            product = Product(
                user_id=current_user.id,
                name=form.name.strip(),
                description=form.description.strip(),
                raw_ingredients={"items": form.ingredients},
            )
            self.session.add(product)
            await self.session.flush()
            product_id = product.id

            classification = Classification(
                product_id=product.id,
                category=engine_result.category,
                regulatory_pathway=engine_result.regulatory_pathway,
                reasoning=engine_result.reasoning,
                rules_fired=engine_result.rules_fired,
            )
            self.session.add(classification)
            await self.session.commit()
            await self.session.refresh(classification)
            classification_id = classification.id

        return ClassificationResponse(
            id=classification_id,
            product_id=product_id,
            category=engine_result.category,
            category_name=engine_result.category_name,
            regulatory_pathway=engine_result.regulatory_pathway,
            reasoning=engine_result.reasoning,
            rules_fired=engine_result.rules_fired,
            is_reconciled=engine_result.is_reconciled,
            user_selected_category=engine_result.user_selected_category,
            ip_protection_map=engine_result.ip_protection_map,
        )
