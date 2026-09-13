import axios from "axios";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: `${BASE}/api/v1`,
  headers: { "Content-Type": "application/json" },
  timeout: 120_000,
});

apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    const msg =
      error.response?.data?.message ||
      error.response?.data?.detail ||
      error.message ||
      "An unexpected error occurred";
    return Promise.reject(new Error(msg));
  }
);

// ── Matters ────────────────────────────────────────────────────────────────────
export const mattersApi = {
  list: () => apiClient.get("/matters").then((r) => r.data),
  get: (id: string) => apiClient.get(`/matters/${id}`).then((r) => r.data),
  create: (data: { title: string; document_type?: string; use_default_templates?: boolean }) =>
    apiClient.post("/matters", data).then((r) => r.data),
  createDemo: () => apiClient.post("/matters/demo").then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/matters/${id}`),
};

// ── Documents ──────────────────────────────────────────────────────────────────
export const documentsApi = {
  list: (matterId: string) =>
    apiClient.get(`/matters/${matterId}/documents`).then((r) => r.data),
  upload: (matterId: string, formData: FormData) =>
    axios
      .post(`${BASE}/api/v1/matters/${matterId}/documents`, formData, {
        timeout: 30_000,
      })
      .then((r) => r.data)
      .catch((error) => {
        const msg =
          error.response?.data?.detail ||
          error.response?.data?.message ||
          error.message ||
          "Document upload failed";
        throw new Error(msg);
      }),
};

// ── Extraction ─────────────────────────────────────────────────────────────────
export const extractionApi = {
  extract: (matterId: string) =>
    apiClient.post(`/matters/${matterId}/extract`).then((r) => r.data),
  getCaseData: (matterId: string) =>
    apiClient.get(`/matters/${matterId}/case-data`).then((r) => r.data),
};

// ── Generation ─────────────────────────────────────────────────────────────────
export const generationApi = {
  generate: (matterId: string, options?: { demo_mode?: boolean }) =>
    apiClient.post(`/matters/${matterId}/generate`, options || {}).then((r) => r.data),
  listRuns: (matterId: string) =>
    apiClient.get(`/matters/${matterId}/generation-runs`).then((r) => r.data),
  downloadUrl: (runId: string) =>
    `${BASE}/api/v1/generation-runs/${runId}/download`,
};

// ── Validation ─────────────────────────────────────────────────────────────────
export const validationApi = {
  validate: (runId: string) =>
    apiClient.post(`/generation-runs/${runId}/validate`).then((r) => r.data),
  getResult: (runId: string) =>
    apiClient.get(`/generation-runs/${runId}/validation`).then((r) => r.data),
};

// ── Evaluation ─────────────────────────────────────────────────────────────────
export const evaluationApi = {
  getReport: (runId: string) =>
    apiClient.get(`/generation-runs/${runId}/evaluation`).then((r) => r.data),
  downloadUrl: (runId: string, format?: "markdown" | "json" | "docx") =>
    `${BASE}/api/v1/generation-runs/${runId}/evaluation/download?format=${format || "markdown"}`,
};

// ── Health ─────────────────────────────────────────────────────────────────────
export const healthApi = {
  check: () => apiClient.get("/health").then((r) => r.data),
};
