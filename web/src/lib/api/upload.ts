import { api } from "./browser";

/** Sends `{ file }` as multipart/form-data; the browser adds the boundary. */
function asFormData(body: { file: Blob }) {
  const form = new FormData();
  form.append("file", body.file);
  return form;
}

/** Uploads a PDF to a client's project (Client Components only). */
export function uploadProjectDocument(projectId: number, file: File) {
  return api.POST("/api/projects/{project_id}/documents", {
    params: { path: { project_id: projectId } },
    body: { file },
    bodySerializer: asFormData,
  });
}

/** Where a regulation applies: no type and no project means every project. */
export type RegulationLevel = {
  scope: "client" | "reviewer";
  project_type_id?: number;
  project_id?: number;
};

/** Uploads a regulation PDF at one level (Client Components only). */
export function uploadRegulationDocument(level: RegulationLevel, file: File) {
  return api.POST("/api/regulations/documents", {
    params: { query: level },
    body: { file },
    bodySerializer: asFormData,
  });
}
