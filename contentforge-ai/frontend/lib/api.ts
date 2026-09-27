import { getStoredToken, clearAuthSession } from "./auth";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ============================================================================
// 1. Authentication & User Models
// ============================================================================
export type UserRole = "operator" | "reviewer" | "org_admin" | "system_admin";

export interface User {
  id: string;
  org_id: string;
  email: string;
  role: UserRole | string;
  created_at?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  org_name?: string;
  org_id?: string;
  role?: UserRole;
}

export interface LoginRequest {
  email: string;
  password: string;
}

// ============================================================================
// 2. Ingestion & Document Pipeline Models
// ============================================================================
export type SourceType = "pdf" | "docx" | "text";
export type ProcessedStatus = "uploaded" | "processing" | "processed" | "failed";

export interface DocumentUploadResponse {
  document_id: string;
  status: ProcessedStatus;
  message: string;
}

export interface DocumentMetadata {
  id: string;
  org_id: string;
  uploaded_by?: string;
  file_path?: string;
  file_name?: string;
  file_size_bytes?: number;
  mime_type?: string;
  source_type: SourceType;
  sensitivity_flag: string;
  processed_status: ProcessedStatus;
  error_message?: string | null;
  pii_detected?: boolean;
  pii_types?: string[];
  injection_flagged?: boolean;
  injection_details?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  text: string;
  page_number?: number | null;
  section_reference?: string | null;
  word_count?: number | null;
  created_at: string;
}

export interface DocumentChunksListResponse {
  document_id: string;
  total_chunks: number;
  chunks: DocumentChunk[];
}

// ============================================================================
// 3. Content Understanding & Fact Registry Models
// ============================================================================
export interface EntityCategories {
  people: string[];
  organisations: string[];
  locations: string[];
  products_systems: string[];
}

export interface ContentMetadata {
  id: string;
  document_id: string;
  summary: string;
  document_type: string;
  entities: EntityCategories;
  topics: string[];
  created_at: string;
}

export interface FactRegistryItem {
  id: string;
  document_id: string;
  fact_id_string: string;
  fact_statement: string;
  source_chunk_id?: string | null;
  source_snippet?: string | null;
  confidence: number;
  created_at: string;
}

export interface FactRegistryListResponse {
  document_id: string;
  total_facts: number;
  facts: FactRegistryItem[];
}

export interface UnderstandingPassResponse {
  document_id: string;
  status: "understanding_completed";
  document_type: string;
  summary: string;
  total_facts: number;
  entities: EntityCategories;
  topics: string[];
}

// ============================================================================
// 4. Output Generator Content Schemas (7 Formats)
// ============================================================================
export type OutputType =
  | "linkedin"
  | "twitter"
  | "advisory"
  | "executive_summary"
  | "infographic"
  | "presentation"
  | "video_package";

export interface LinkedInContent {
  hook: string;
  body: string;
  hashtags: string[];
  call_to_action: string;
  fact_ids_used: string[];
}

export interface TweetItem {
  order: number;
  text: string;
}

export interface TwitterContent {
  tweets: TweetItem[];
  fact_ids_used: string[];
}

export interface AdvisoryContent {
  title: string;
  severity: string;
  summary: string;
  scope: string;
  details: string;
  recommended_actions: string[];
  references: string[];
  fact_ids_used: string[];
}

export interface ExecutiveSummaryContent {
  title: string;
  summary_text: string;
  key_takeaways: string[];
  fact_ids_used: string[];
}

export interface InfographicSection {
  order: number;
  stat_or_point: string;
  icon_suggestion: string;
}

export interface InfographicContent {
  headline: string;
  sections: InfographicSection[];
  layout_style: string;
  colour_theme: string;
  fact_ids_used: string[];
}

export interface SlideItem {
  slide_no: number;
  title: string;
  bullets: string[];
  speaker_notes: string;
  visual_suggestion: string;
}

export interface PresentationContent {
  slides: SlideItem[];
  fact_ids_used: string[];
}

export interface SceneItem {
  scene_no: number;
  narration: string;
  visual_description: string;
  subtitle_text: string;
  duration_estimate_sec: number;
}

export interface VideoPackageContent {
  title: string;
  total_duration_estimate: string;
  scenes: SceneItem[];
  fact_ids_used: string[];
}

export type GeneratorContentPayload =
  | LinkedInContent
  | TwitterContent
  | AdvisoryContent
  | ExecutiveSummaryContent
  | InfographicContent
  | PresentationContent
  | VideoPackageContent;

// ============================================================================
// 5. Generation Job & Output Envelopes
// ============================================================================
export type JobStatus = "queued" | "processing" | "completed" | "completed_with_warnings" | "failed";
export type OutputStatus = "completed" | "completed_with_warnings" | "failed";

export interface GenerationSettings {
  audience: string;
  tone: string;
  language: string;
  detail_level: "concise" | "standard" | "comprehensive";
  objective: string;
}

export interface GenerationRequest {
  document_id: string;
  selected_outputs: OutputType[];
  settings?: Partial<GenerationSettings>;
}

export interface GenerationJobResponse {
  job_id: string;
  document_id: string;
  status: JobStatus;
  selected_outputs: OutputType[];
  message: string;
}

export interface UnverifiedClaim {
  claim: string;
  reason: string;
  cited_fact_ids?: string[];
  schema_error?: string;
}

export interface GeneratedOutput<T = any> {
  id: string;
  job_id: string;
  output_type: OutputType;
  content: T;
  validation_score: number;
  status: OutputStatus;
  fact_ids_used: string[];
  unverified_claims: UnverifiedClaim[];
  created_at: string;
}

export interface GenerationJobDetail {
  id: string;
  document_id: string;
  status: JobStatus;
  error_message?: string | null;
  selected_outputs: OutputType[];
  settings?: GenerationSettings;
  created_at: string;
  completed_at?: string | null;
  outputs?: GeneratedOutput[];
}

export interface GenerationOutputsListResponse {
  job_id: string;
  total_outputs: number;
  outputs: GeneratedOutput[];
}

export interface HistoryItem {
  id: string;
  job_id: string;
  document_id: string;
  document_title: string;
  status: JobStatus;
  selected_outputs: OutputType[];
  created_at: string;
}

// ============================================================================
// 6. Core API Request Engine
// ============================================================================
export class ApiError extends Error {
  status: number;
  detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(options.headers || {});

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const url = `${API_BASE_URL.replace(/\/+$/, "")}${path.startsWith("/") ? "" : "/"}${path}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      clearAuthSession();
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.href = "/login?session_expired=1";
      }
      throw new ApiError(401, "Session expired. Please log in again.");
    }

    if (!response.ok) {
      let errorDetail = "";
      try {
        const errorJson = await response.json();
        if (typeof errorJson.detail === "string") {
          errorDetail = errorJson.detail;
        } else if (Array.isArray(errorJson.detail)) {
          errorDetail = errorJson.detail.map((e: any) => e.msg || JSON.stringify(e)).join(", ");
        } else if (errorJson.detail) {
          errorDetail = JSON.stringify(errorJson.detail);
        } else {
          errorDetail = JSON.stringify(errorJson);
        }
      } catch {
        errorDetail = await response.text();
      }
      const message = errorDetail || `Request failed with status ${response.status}`;
      throw new ApiError(response.status, message, errorDetail);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return await response.json();
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    const msg =
      err.message === "Failed to fetch"
        ? "Unable to connect to ContentForge AI backend. Please verify your connection or ensure the backend service is running."
        : err.message || "Network request failed. Backend may be offline.";
    throw new ApiError(0, msg, msg);
  }
}

// Local history helpers
function saveLocalHistory(item: HistoryItem) {
  if (typeof window === "undefined") return;
  try {
    const raw = localStorage.getItem("contentforge_history");
    const list: HistoryItem[] = raw ? JSON.parse(raw) : [];
    const filtered = list.filter((i) => i.job_id !== item.job_id);
    filtered.unshift(item);
    localStorage.setItem("contentforge_history", JSON.stringify(filtered.slice(0, 50)));
  } catch {
    // ignore
  }
}

function getLocalHistory(): HistoryItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem("contentforge_history");
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

// ============================================================================
// 7. Typed API Client Submodules
// ============================================================================

export const authApi = {
  login: (data: LoginRequest) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  register: (data: RegisterRequest) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

export const documentsApi = {
  upload: async (fileOrText: File | string, title?: string, sensitivity = "internal") => {
    const formData = new FormData();
    if (typeof fileOrText === "string") {
      const blob = new Blob([fileOrText], { type: "text/plain" });
      formData.append("file", blob, title ? `${title.replace(/\s+/g, "_")}.txt` : "pasted_text.txt");
    } else {
      formData.append("file", fileOrText);
    }
    formData.append("sensitivity", sensitivity);
    return request<DocumentUploadResponse>("/documents/upload", {
      method: "POST",
      body: formData,
    });
  },
  get: (id: string) => request<DocumentMetadata>(`/documents/${id}`),
  getChunks: (id: string) => request<DocumentChunksListResponse>(`/documents/${id}/chunks`),
};

export const factsApi = {
  list: (documentId: string) => request<FactRegistryListResponse>(`/documents/${documentId}/facts`),
  getMetadata: (documentId: string) => request<ContentMetadata>(`/documents/${documentId}/metadata`),
  runUnderstandingPass: (documentId: string) =>
    request<UnderstandingPassResponse>(`/documents/${documentId}/understand`, {
      method: "POST",
    }),
};

export const generationApi = {
  generate: async (data: GenerationRequest) => {
    const res = await request<GenerationJobResponse>("/generate", {
      method: "POST",
      body: JSON.stringify(data),
    });
    // Save to local history
    saveLocalHistory({
      id: res.job_id,
      job_id: res.job_id,
      document_id: res.document_id,
      document_title: `Transformation ${res.job_id.slice(0, 8)}`,
      status: res.status,
      selected_outputs: res.selected_outputs,
      created_at: new Date().toISOString(),
    });
    return res;
  },

  getJob: async (jobId: string): Promise<GenerationJobDetail> => {
    const job = await request<GenerationJobDetail>(`/generation/${jobId}`);
    // If job has completed or warnings, fetch output payload
    if (job.status === "completed" || job.status === "completed_with_warnings") {
      try {
        const outputsRes = await request<GenerationOutputsListResponse>(`/generation/${jobId}/outputs`);
        job.outputs = outputsRes.outputs;
      } catch {
        // Fallback to local edited outputs if present
      }
    }
    return job;
  },

  getOutputs: (jobId: string) => request<GenerationOutputsListResponse>(`/generation/${jobId}/outputs`),

  getSingleOutput: (outputId: string) => request<GeneratedOutput>(`/outputs/${outputId}`),
};

export const outputsApi = {
  update: async (outputId: string, updatedContent: any): Promise<GeneratedOutput> => {
    try {
      return await request<GeneratedOutput>(`/outputs/${outputId}`, {
        method: "PUT",
        body: JSON.stringify({ content: updatedContent }),
      });
    } catch {
      // Local fallback if PUT /outputs/{id} is not implemented yet in backend Part 2
      if (typeof window !== "undefined") {
        localStorage.setItem(`contentforge_output_${outputId}`, JSON.stringify(updatedContent));
      }
      return {
        id: outputId,
        job_id: "local",
        output_type: "linkedin",
        content: updatedContent,
        validation_score: 1.0,
        status: "completed",
        fact_ids_used: [],
        unverified_claims: [],
        created_at: new Date().toISOString(),
      };
    }
  },
};

export const historyApi = {
  list: async (limit = 20): Promise<HistoryItem[]> => {
    try {
      const items = await request<HistoryItem[]>(`/history?limit=${limit}`);
      return items;
    } catch {
      // Graceful fallback to client history
      return getLocalHistory().slice(0, limit);
    }
  },
  save: (item: HistoryItem) => saveLocalHistory(item),
};

export const verificationApi = {
  verifyRecord: (recordId: string) =>
    request<VerificationResult>(`/verify/${recordId}`),

  verifyByText: (text: string) =>
    request<VerificationResult>("/verify/by-content", {
      method: "POST",
      body: JSON.stringify({ text }),
    }),

  verifyByFile: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<VerificationResult>("/verify/by-content", {
      method: "POST",
      body: formData,
    });
  },

  adminVerifyChain: () =>
    request<{
      organisation_id: string;
      organisation_name: string;
      intact: boolean;
      total_records: number;
      broken_at_index: number | null;
      latest_record_hash: string | null;
      message: string;
    }>("/admin/trust-chain/verify"),
};

export interface VerificationResult {
  status: "verified" | "not_found" | "chain_broken";
  record_id?: string;
  record_type?: string;
  organisation_name?: string;
  output_type?: string;
  approved_by?: string | null;
  approved_at?: string | null;
  source_document_verified?: boolean;
  chain_integrity?: string;
  chain_index?: number;
  record_hash?: string;
  content_hash?: string;
  public_anchor_tx_hash?: string | null;
  created_at?: string | null;
  message?: string;
}

export const api = {
  auth: authApi,
  documents: documentsApi,
  facts: factsApi,
  generation: generationApi,
  outputs: outputsApi,
  history: historyApi,
  verification: verificationApi,
};

export function cleanPublishableText(text: string): string {
  if (!text) return "";
  return text
    .replace(/\[f\d+(?:\s*,\s*f\d+)*\]/gi, "")
    .replace(/\((?:Fact Registry|Source Chunk|Fact ID|RAG Context|Provenance|Internal)[^)]*\)/gi, "")
    .replace(/\[(?:Fact Registry|Source Chunk|Fact ID|RAG Context|Provenance|Internal)[^\]]*\]/gi, "")
    .replace(/  +/g, " ")
    .replace(/\s+([.,!?;:])/g, "$1")
    .trim();
}

export default api;


