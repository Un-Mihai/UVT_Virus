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

/** Uploads a regulation PDF to one rule set of a project type (Client Components only). */
export function uploadRegulationDocument(
  projectTypeId: number,
  scope: "client" | "reviewer",
  file: File,
) {
  return api.POST(
    "/api/project-types/{project_type_id}/regulations/{scope}/documents",
    {
      params: { path: { project_type_id: projectTypeId, scope } },
      body: { file },
      bodySerializer: asFormData,
    },
  );
}
