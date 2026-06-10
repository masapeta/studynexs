"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

const trendGlyph: Record<string, { glyph: string; color: string; label: string }> = {
  improving: { glyph: "▲", color: "var(--success, #059669)", label: "Improving" },
  stable: { glyph: "▬", color: "var(--text-muted)", label: "Stable" },
  declining: { glyph: "▼", color: "var(--danger)", label: "Declining" },
  insufficient: { glyph: "·", color: "var(--text-muted)", label: "Too few assessments" },
};

function barColor(pct: number) {
  if (pct < 40) return "var(--danger)";
  if (pct < 60) return "var(--warning, #d97706)";
  return "var(--success, #059669)";
}

/** Per-topic mastery bars with class-average ticks — every number traces back
 * to real exam scores (hover history), nothing is model-generated. */
export default function TopicMasterySection({ studentId }: { studentId: string }) {
  const router = useRouter();
  const [subjects, setSubjects] = useState<any[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!studentId) return;
    api(`/api/v1/mastery/students/${studentId}`)
      .then((r) => setSubjects(r.data?.subjects || []))
      .catch(() => {})
      .finally(() => setLoaded(true));
  }, [studentId]);

  if (!loaded || subjects.length === 0) return null; // nothing tracked yet — stay quiet

  return (
    <div className="card" style={{ padding: 24 }}>
      <h2 style={{ fontSize: 15, fontWeight: 700, margin: "0 0 16px" }}>Topic Mastery</h2>
      {subjects.map((subj) => (
        <div key={subj.subject_id} style={{ marginBottom: 18 }}>
          <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>{subj.subject_name}</div>
          {subj.topics.map((t: any) => {
            const trend = trendGlyph[t.trend] || trendGlyph.insufficient;
            const historyTip = (t.history || [])
              .map((h: any) => `${h.date} ${h.title}: ${h.pct}%`)
              .join("\n");
            return (
              <div key={t.topic} style={{ display: "flex", alignItems: "center", gap: 10, padding: "5px 0" }} title={historyTip}>
                <div style={{ width: 160, fontSize: 13, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {t.topic_display}
                </div>
                <div style={{ flex: 1, position: "relative", height: 10, background: "var(--border-light, #eee)", borderRadius: 5 }}>
                  <div style={{ position: "absolute", inset: 0, width: `${Math.min(t.mastery_pct, 100)}%`, background: barColor(t.mastery_pct), borderRadius: 5 }} />
                  {t.class_avg_pct != null && (
                    <div
                      title={`Class average ${t.class_avg_pct}%`}
                      style={{ position: "absolute", top: -3, bottom: -3, left: `${Math.min(t.class_avg_pct, 100)}%`, width: 2, background: "var(--text-secondary)" }}
                    />
                  )}
                </div>
                <div style={{ width: 48, textAlign: "right", fontWeight: 700, fontSize: 13 }}>{Math.round(t.mastery_pct)}%</div>
                <div style={{ width: 18, textAlign: "center", color: trend.color }} title={trend.label}>{trend.glyph}</div>
                <button
                  className="btn btn-ghost"
                  style={{ width: "auto", padding: "3px 10px", fontSize: 12, borderRadius: "var(--radius-full)" }}
                  title="Generate a practice paper on this topic"
                  onClick={() =>
                    router.push(
                      `/dashboard/ai-papers?class_id=${subj.class_id}&subject_id=${subj.subject_id}&topics=${encodeURIComponent(t.topic_display)}&difficulty=easy`
                    )
                  }
                >
                  Practice
                </button>
              </div>
            );
          })}
        </div>
      ))}
      <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
        Weighted by exam type and recency. The grey tick is the class average. Hover a row for the underlying scores.
      </div>
    </div>
  );
}
