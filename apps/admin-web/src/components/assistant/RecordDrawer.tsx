"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ExternalLink, Lock, X } from "lucide-react";
import { api, ApiError, getApiErrorMessage } from "@/lib/api";
import { useAssistant } from "./AssistantProvider";

type StudentProfile = {
  student_name: string;
  admission_no: string;
  roll_no?: string | null;
  class_name: string;
  status: string;
  attendance?: { percentage?: number | null; total?: number } | null;
};

type ClassInfo = {
  grade: string;
  section: string;
  class_incharge_name?: string | null;
  student_count?: number;
  attendance_pct?: number | null;
};

type State =
  | { kind: "loading" }
  | { kind: "denied" }
  | { kind: "error"; message: string }
  | { kind: "student"; data: StudentProfile }
  | { kind: "class"; data: ClassInfo };

/** In-place record summary for chat results. Reuses existing authorised read endpoints only. */
export function RecordDrawer() {
  const { record, closeRecord } = useAssistant();
  const [state, setState] = useState<State>({ kind: "loading" });
  const closeRef = useRef<HTMLButtonElement>(null);
  const returnFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!record) return;
    returnFocus.current = document.activeElement as HTMLElement | null;
    let alive = true;
    const url =
      record.kind === "student"
        ? `/api/v1/academic/students/${record.id}/profile`
        : `/api/v1/academic/classes/${record.id}`;
    api<{ data: StudentProfile | ClassInfo }>(url)
      .then((r) => {
        if (!alive) return;
        setState(
          record.kind === "student"
            ? { kind: "student", data: r.data as StudentProfile }
            : { kind: "class", data: r.data as ClassInfo }
        );
      })
      .catch((e) => {
        if (!alive) return;
        if (e instanceof ApiError && (e.status === 403 || e.status === 404)) setState({ kind: "denied" });
        else setState({ kind: "error", message: getApiErrorMessage(e, "Couldn't load this record.") });
      });
    setTimeout(() => closeRef.current?.focus(), 20);
    const onKey = (ev: KeyboardEvent) => {
      if (ev.key === "Escape") closeRecord();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      alive = false;
      setState({ kind: "loading" });
      window.removeEventListener("keydown", onKey);
      returnFocus.current?.focus?.();
    };
  }, [record, closeRecord]);

  if (!record) return null;
  const title = record.kind === "student" ? "Student" : "Class";

  return (
    <div role="dialog" aria-modal="true" aria-label={`${title} summary`} className="sn-asst-drawer">
      <div className="sn-asst-drawer__scrim" onClick={closeRecord} aria-hidden />
      <div className="sn-asst-drawer__sheet">
        <div className="sn-ws-panel__head">
          <button type="button" className="btn btn-ghost gw-btn-sm" onClick={closeRecord}>
            <ArrowLeft size={14} aria-hidden /> Back
          </button>
          <strong className="sn-ws-panel__title">{title}</strong>
          <button ref={closeRef} type="button" className="sn-ws-panel__close" onClick={closeRecord}
                  aria-label="Close">
            <X size={16} />
          </button>
        </div>
        <div className="sn-ws-panel__body">
          {state.kind === "loading" && <div className="spinner" style={{ margin: "24px auto" }} aria-label="Loading" />}
          {state.kind === "denied" && (
            <div className="sn-asst-muted" role="status">
              <Lock size={16} aria-hidden /> This record isn&apos;t available to your role.
            </div>
          )}
          {state.kind === "error" && <div className="sn-inline-alert sn-inline-alert--error" role="alert">{state.message}</div>}
          {state.kind === "student" && (
            <dl className="sn-asst-facts">
              <dt>Name</dt><dd>{state.data.student_name}</dd>
              <dt>Admission no.</dt><dd>{state.data.admission_no}</dd>
              <dt>Class</dt><dd>{state.data.class_name}{state.data.roll_no ? ` · Roll ${state.data.roll_no}` : ""}</dd>
              <dt>Status</dt><dd>{state.data.status}</dd>
              <dt>Attendance</dt>
              <dd>{state.data.attendance?.percentage != null ? `${state.data.attendance.percentage}%` : "Not recorded yet"}</dd>
            </dl>
          )}
          {state.kind === "class" && (
            <dl className="sn-asst-facts">
              <dt>Class</dt><dd>{state.data.grade} - {state.data.section}</dd>
              <dt>Incharge</dt><dd>{state.data.class_incharge_name || "Not assigned"}</dd>
              <dt>Students</dt><dd>{state.data.student_count ?? "—"}</dd>
              <dt>Attendance</dt>
              <dd>{state.data.attendance_pct != null ? `${state.data.attendance_pct}%` : "Not recorded yet"}</dd>
            </dl>
          )}
          {state.kind !== "denied" && (
            <Link href={record.href} className="btn btn-primary" onClick={closeRecord} style={{ width: "auto" }}>
              Open full page <ExternalLink size={14} aria-hidden />
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
