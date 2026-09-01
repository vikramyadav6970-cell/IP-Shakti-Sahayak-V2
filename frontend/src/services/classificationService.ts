import { api } from "./apiClient";
import { ProductCategory } from "@/types";

export interface FormulationPayload {
  name: string;
  description: string;
  ingredients: string[];
  has_classical_text_reference?: boolean;
  classical_text_name?: string;
  is_strict_classical_recipe?: boolean;
  has_novel_excipients_or_delivery?: boolean;
  is_purified_standardized_fraction?: boolean;
  is_food_or_dietary_supplement?: boolean;
  has_synthetic_additives?: boolean;
  target_market?: string;
  user_selected_category?: ProductCategory | string;
}

export interface ClassificationApiResponse {
  id?: string;
  product_id?: string;
  category: ProductCategory;
  category_name: string;
  regulatory_pathway: string;
  reasoning?: string;
  rules_fired: string[];
  is_reconciled: boolean;
  user_selected_category?: string;
  ip_protection_map: {
    patent: {
      eligibility: string;
      reason: string;
      action: string;
    };
    trademark: {
      eligibility: string;
      nice_class: string;
      action: string;
    };
    abs: {
      eligibility: string;
      action: string;
    };
  };
}

export const classificationService = {
  classify: async (payload: FormulationPayload): Promise<ClassificationApiResponse> => {
    return await api.post<ClassificationApiResponse>("/api/v1/classification", payload);
  },
};
