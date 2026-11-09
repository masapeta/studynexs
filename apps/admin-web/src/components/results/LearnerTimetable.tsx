"use client";

import { useEffect, useState } from "react";
import { CalendarDays } from "lucide-react";
import { Card, EmptyState, SectionHeader, SkeletonCard } from "@/components/ui/kit";
import { api, getApiErrorMessage } from "@/lib/api";

type Slot = {
  id: string;
  day_of_week: string;
  period_number: number;
  start_time: string;
  end_time: string;
  subject_name: string | null;
  teacher_name: string | null;
};

const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];

/** Read-only class timetable for a student (self) or a parent's linked child (server-scoped). */
export function LearnerTimetable({ endpoint, title = "Timetable" }: { endpoint: string; title?: string }) {
  const [slots, setSlots] = useState<Slot[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    api<{ data: Slot[] }>(endpoint)
      .then((r) => alive && setSlots(r.data))
      .catch((e) => alive && setError(getApiErrorMessage(e, "Couldn't load the timetable.")));
    return () => {
      alive = false;
    };
  }, [endpoint]);

  if (error) return <p role="alert" style={{ color: "var(--danger)" }}>{error}</p>;
  if (slots === null) return <SkeletonCard />;
  if (slots.length === 0) {
    return <EmptyState icon={CalendarDays} title="No timetable yet" message="The school hasn't published a timetable for this class." />;
  }
  return (
    <section aria-label={title}>
      <SectionHeader title={title} />
      <Card padded={false}>
        <div className="sn-table-scroll">
          <table className="data-table" data-testid="learner-timetable">
            <thead>
              <tr><th scope="col">Day</th><th scope="col">Period</th><th scope="col">Time</th><th scope="col">Subject</th><th scope="col">Teacher</th></tr>
            </thead>
            <tbody>
              {[...slots]
                .sort((a, b) => DAYS.indexOf(a.day_of_week) - DAYS.indexOf(b.day_of_week) || a.period_number - b.period_number)
                .map((s) => (
                  <tr key={s.id}>
                    <td style={{ textTransform: "capitalize" }}>{s.day_of_week}</td>
                    <td>{s.period_number}</td>
                    <td>{s.start_time}–{s.end_time}</td>
                    <td>{s.subject_name ?? "—"}</td>
                    <td>{s.teacher_name ?? "—"}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </Card>
    </section>
  );
}
