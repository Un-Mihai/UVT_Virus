import type { StatusState } from "@/components/status-word";
import type { components } from "@/lib/api/schema";

type ProjectSummary = components["schemas"]["ProjectSummary"];
type Project = Pick<ProjectSummary, "status" | "in_review" | "verdict">;

/** Where a file stands for its applicant: not sent, waiting for a reviewer, being reviewed, or decided. */
export function fileState({ status, in_review, verdict }: Project): {
  key: "draft" | "waiting" | "inReview" | "approved" | "changesRequested";
  state: StatusState;
} {
  if (verdict === "approved") return { key: "approved", state: "ok" };
  if (verdict === "changes_requested")
    return { key: "changesRequested", state: "warn" };
  if (status === "draft") return { key: "draft", state: "neutral" };
  return in_review
    ? { key: "inReview", state: "warn" }
    : { key: "waiting", state: "neutral" };
}

/** Who applied: the organisation from the form, and the account that filed it when it differs. */
export function applicantOf(
  {
    applicant_name,
    owner_name,
  }: Pick<ProjectSummary, "applicant_name" | "owner_name">,
  unnamed: string,
): { name: string; account: string | null } {
  return {
    name: applicant_name ?? owner_name ?? unnamed,
    account: applicant_name && owner_name ? owner_name : null,
  };
}
