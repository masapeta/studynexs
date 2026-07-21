"use client";

import { useMemo, useState } from "react";

export type ClassAttendanceBar = {
  label: string;
  present?: number;
  strength?: number;
  percentage: number;
  date?: string;
};

type Props = {
  data: ClassAttendanceBar[];
};

const Y_TICKS = [100, 75, 50, 25, 0];

function shortClassLabel(label: string) {
  return label.replace(/\s*-\s*/g, "-");
}

export function formatAttendanceChartDate(iso?: string) {
  if (!iso) return null;
  const parsed = new Date(`${iso}T12:00:00`);
  if (Number.isNaN(parsed.getTime())) return null;
  const today = new Date();
  const sameDay =
    parsed.getFullYear() === today.getFullYear() &&
    parsed.getMonth() === today.getMonth() &&
    parsed.getDate() === today.getDate();
  if (sameDay) return "Today";
  return parsed.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function ClassAttendanceChart({ data }: Props) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  const bars = useMemo(
    () =>
      data.map((item) => ({
        ...item,
        present: item.present ?? 0,
        strength: item.strength ?? 0,
        percentage: Math.max(0, Math.min(100, Number(item.percentage) || 0)),
      })),
    [data]
  );

  const columnCount = Math.max(bars.length, 1);

  if (bars.length === 0) {
    return <p className="gw-muted">No class attendance data yet.</p>;
  }

  return (
    <div
      className="class-attendance-chart"
      role="group"
      aria-label="Class attendance — hover a bar for present versus class strength"
      style={{ ["--attendance-columns" as string]: columnCount }}
    >
      <div className="class-attendance-chart__body">
        <div className="class-attendance-chart__y-axis" aria-hidden>
          {Y_TICKS.map((tick) => (
            <span key={tick} className="class-attendance-chart__y-tick">
              {tick}
            </span>
          ))}
        </div>

        <div className="class-attendance-chart__plot-wrap">
          <div className="class-attendance-chart__grid-lines" aria-hidden>
            {Y_TICKS.map((tick) => (
              <span key={tick} className="class-attendance-chart__grid-line" />
            ))}
          </div>

          <div className="class-attendance-chart__plot">
            {bars.map((item, index) => {
              const isActive = activeIndex === index;

              return (
                <div key={item.label} className="class-attendance-chart__column">
                  <div className="class-attendance-chart__bar-slot">
                    {isActive ? (
                      <div className="class-attendance-chart__tooltip" role="tooltip">
                        <strong>
                          {item.present} / {item.strength}
                        </strong>
                        <span>present</span>
                      </div>
                    ) : null}

                    <button
                      type="button"
                      className={`class-attendance-chart__track${isActive ? " is-active" : ""}`}
                      aria-label={`${item.label}: ${item.present} of ${item.strength} students present, ${item.percentage}%`}
                      onMouseEnter={() => setActiveIndex(index)}
                      onMouseLeave={() => setActiveIndex(null)}
                      onFocus={() => setActiveIndex(index)}
                      onBlur={() => setActiveIndex(null)}
                    >
                      {item.percentage > 0 ? (
                        <span
                          className="class-attendance-chart__fill"
                          style={{ height: `${item.percentage}%` }}
                          aria-hidden
                        />
                      ) : null}
                    </button>
                  </div>

                  <span className="class-attendance-chart__x-label" title={item.label}>
                    {shortClassLabel(item.label)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
