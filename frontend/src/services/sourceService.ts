import { api } from "./apiClient";

export interface CollectionMeta {
  id: string;
  name: string;
  description: string;
  jurisdiction: string;
  official_authority: string;
}

export interface SourcesOverviewResponse {
  collections: CollectionMeta[];
  total_documents_indexed: number;
  verification_rate: number;
  last_synced_wipo: string;
  jurisdictions: string[];
}

export interface SourceDocument {
  id: string;
  title: string;
  jurisdiction: string;
  document_type: string;
  collection: string;
  key_provisions: string[];
  official_url: string;
  verification_status: string;
}

export const sourceService = {
  getOverview: async (): Promise<SourcesOverviewResponse> => {
    return await api.get<SourcesOverviewResponse>("/api/v1/sources/overview");
  },
  getDocuments: async (): Promise<SourceDocument[]> => {
    return await api.get<SourceDocument[]>("/api/v1/sources/documents");
  },
};
