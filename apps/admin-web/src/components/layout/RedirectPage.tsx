"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/** Client redirect for legacy routes (preserves bookmarks). */
export function RedirectPage({ to }: { to: string }) {
  const router = useRouter();
  useEffect(() => {
    router.replace(to);
  }, [router, to]);
  return (
    <div className="gw-center" style={{ minHeight: "40vh" }}>
      <div className="spinner" />
    </div>
  );
}
