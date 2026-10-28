import { notFound } from "next/navigation";

// Unknown paths under a language get the styled not-found page instead of Next's bare one.
export default function MissingPage() {
  notFound();
}
