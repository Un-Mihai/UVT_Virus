"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

/** Re-renders the page's Server Components every few seconds while work runs in the API
 *  (a verification, OCR of scanned pages), so its progress shows without a reload. */
export function RefreshWhile({
  active,
  every = 2500,
}: {
  active: boolean;
  every?: number;
}) {
  const router = useRouter();
  useEffect(() => {
    if (!active) return;
    const timer = setInterval(() => router.refresh(), every);
    return () => clearInterval(timer);
  }, [active, every, router]);
  return null;
}
