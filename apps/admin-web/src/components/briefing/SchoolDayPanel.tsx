"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Clock } from "lucide-react";
import { api } from "@/lib/api";
import { AppSelect } from "@/components/ui/AppSelect";
import { formatClassLabel, parseHm, sortClasses, todayDayKey } from "@/lib/format";

export type TimetablePeriod = {
  period: string;
  time: string;
  label: string;
  endMin: number;
};

type ClassRow = { id: string; grade: string; section: string };

type TimetableSlot = {
  period_number: number;
  start_time: string;
  end_time: string;
  subject_name?: string | null;
  day_of_week: string;
};

function buildPeriods(slots: TimetableSlot[]): TimetablePeriod[] {
  const day = todayDayKey();
  const today = slots
    .filter((s) => s.day_of_week?.toLowerCase() === day)
    .sort((a, b) => a.period_number - b.period_number || parseHm(a.start_time) - parseHm(b.start_time));

  return today.map((s) => ({
    period: `P${s.period_number}`,
    time: s.start_time,
    label: s.subject_name || "Period",
    endMin: parseHm(s.end_time || s.start_time) || parseHm(s.start_time) + 45,
  }));
}

function SchoolDayTimeline({ periods }: { periods: TimetablePeriod[] }) {
  const now = new Date();
  const mins = now.getHours() * 60 + now.getMinutes();
  let activeIdx = -1;
  periods.forEach((p, i) => {
    const start = parseHm(p.time);
    if (mins >= start && mins < p.endMin) activeIdx = i;
    else if (mins >= start) activeIdx = i;
  });

  if (!periods.length) {
    return (
      <p className="briefing-muted-text">
        No periods scheduled for today.{" "}
        <Link href="/dashboard/timetable" className="briefing-link">
          Set up timetable →
        </Link>
      </p>
    );
  }

  return (
    <div className="briefing-timeline">
      <div className="briefing-timeline-rail" />
      {periods.map((p, i) => {
        const active = i === activeIdx;
        const past = activeIdx > i;
        const isBreak = /break|lunch/i.test(p.label);
        return (
          <div key={`${p.period}-${p.time}`} className="briefing-timeline-item">
            <span
              className={`briefing-timeline-dot ${active ? "active" : ""} ${past ? "past" : ""}`}
            />
            <div className="briefing-timeline-row">
              <span
                className={`briefing-timeline-label ${active ? "active" : ""} ${past ? "past" : ""}`}
              >
                {isBreak ? p.label : `${p.period} · ${p.label}`}
              </span>
              <span className="briefing-timeline-time">{p.time}</span>
            </div>
            {active && !isBreak && (
              <span className="briefing-timeline-now">in session now</span>
            )}
          </div>
        );
      })}
    </div>
  );
}

type Props = {
  defaultClassId?: string | null;
};

export function SchoolDayPanel({ defaultClassId }: Props) {
  const [classes, setClasses] = useState<ClassRow[]>([]);
  const [classId, setClassId] = useState("");
  const [periods, setPeriods] = useState<TimetablePeriod[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api("/api/v1/academic/classes?page_size=100")
      .then((r) => {
        const items = sortClasses<any>(r.items || r.data || []);
        setClasses(items);
        const preferred =
          defaultClassId && items.some((c: ClassRow) => c.id === defaultClassId)
            ? defaultClassId
            : items[0]?.id || "";
        setClassId(preferred);
      })
      .catch(() => {
        setClasses([]);
        setLoading(false);
      });
  }, [defaultClassId]);

  useEffect(() => {
    if (!classId) {
      setPeriods([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    api<{ data: TimetableSlot[] }>(`/api/v1/timetable/class/${classId}`)
      .then((tt) => setPeriods(buildPeriods(tt.data || [])))
      .catch(() => setPeriods([]))
      .finally(() => setLoading(false));
  }, [classId]);

  return (
    <div className="briefing-card briefing-panel">
      <div className="briefing-panel-head briefing-school-day-head">
        <div className="briefing-school-day-title">
          <Clock size={16} className="briefing-tone-brass" aria-hidden />
          <h3>Today&apos;s school day</h3>
        </div>
        {classes.length > 0 && (
          <AppSelect
            variant="pill"
            value={classId}
            onChange={setClassId}
            aria-label="Select class and section"
            options={classes.map((c) => ({
              value: c.id,
              label: formatClassLabel(c.grade, c.section),
            }))}
          />
        )}
      </div>
      {loading ? (
        <div className="gw-center" style={{ padding: "1.5rem 0" }}>
          <div className="spinner" />
        </div>
      ) : (
        <SchoolDayTimeline periods={periods} />
      )}
    </div>
  );
}
