"use client";

import { Suspense } from "react";
import StudentTutorPage from "./tutor-page";

export default function Page() {
  return (
    <Suspense fallback={<div style={{ padding: 40, textAlign: "center" }}><div className="spinner" style={{ margin: "0 auto" }} /></div>}>
      <StudentTutorPage />
    </Suspense>
  );
}
