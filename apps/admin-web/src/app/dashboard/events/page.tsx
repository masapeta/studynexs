"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { CalendarDays, MapPin, Plus } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";
import { eventBadgeParts } from "@/lib/format";
import { PageShell } from "@/components/layout/PageShell";
import { StatusBadge } from "@/components/briefing/StatusBadge";

type EventItem = {
  id: string;
  title: string;
  description?: string | null;
  event_date: string;
  event_time?: string | null;
  venue?: string | null;
};

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const FILTERS = [
  { key: "all", label: "Total events" },
  { key: "this_month", label: "This month" },
  { key: "upcoming", label: "Upcoming" },
] as const;

type EventFilter = (typeof FILTERS)[number]["key"];

function monthLabel(year: number, month: number) {
  return new Date(year, month, 1).toLocaleDateString("en-IN", { month: "long", year: "numeric" });
}

export default function EventsPage() {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [saving, setSaving] = useState(false);
  const [viewMonth, setViewMonth] = useState(() => new Date().getMonth());
  const [viewYear, setViewYear] = useState(() => new Date().getFullYear());
  const [listFilter, setListFilter] = useState<EventFilter>("all");
  const [form, setForm] = useState({
    title: "",
    event_date: new Date().toISOString().split("T")[0],
    venue: "",
    description: "",
  });

  function load() {
    setLoading(true);
    api<{ data: EventItem[] }>("/api/v1/ops/events")
      .then((r) => setEvents(r.data || []))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load events")))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  const eventDates = useMemo(() => {
    const set = new Set<string>();
    events.forEach((e) => {
      const d = e.event_date?.slice(0, 10);
      if (d) set.add(d);
    });
    return set;
  }, [events]);

  const calendarCells = useMemo(() => {
    const first = new Date(viewYear, viewMonth, 1);
    const startOffset = (first.getDay() + 6) % 7;
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
    const cells: ({ day: number; iso: string } | null)[] = [];
    for (let i = 0; i < startOffset; i++) cells.push(null);
    for (let d = 1; d <= daysInMonth; d++) {
      const iso = `${viewYear}-${String(viewMonth + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      cells.push({ day: d, iso });
    }
    return cells;
  }, [viewMonth, viewYear]);

  const todayIso = new Date().toISOString().slice(0, 10);

  const viewedMonthPrefix = `${viewYear}-${String(viewMonth + 1).padStart(2, "0")}`;

  const counts = useMemo(() => {
    const thisMonth = events.filter((e) => e.event_date?.slice(0, 7) === viewedMonthPrefix).length;
    const upcomingCount = events.filter((e) => (e.event_date?.slice(0, 10) || "") >= todayIso).length;
    return {
      all: events.length,
      this_month: thisMonth,
      upcoming: upcomingCount,
    };
  }, [events, viewedMonthPrefix, todayIso]);

  const upcoming = useMemo(() => {
    let list = [...events].sort(
      (a, b) => new Date(a.event_date).getTime() - new Date(b.event_date).getTime()
    );
    if (listFilter === "this_month") {
      list = list.filter((e) => e.event_date?.slice(0, 7) === viewedMonthPrefix);
    } else if (listFilter === "upcoming") {
      list = list.filter((e) => (e.event_date?.slice(0, 10) || "") >= todayIso);
    }
    return list;
  }, [events, listFilter, viewedMonthPrefix, todayIso]);

  async function addEvent() {
    if (!form.title.trim() || !form.event_date) {
      setError("Title and date are required.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await api("/api/v1/ops/events", {
        method: "POST",
        body: JSON.stringify({
          title: form.title,
          event_date: form.event_date,
          venue: form.venue || null,
          description: form.description || null,
        }),
      });
      setForm({
        title: "",
        event_date: new Date().toISOString().split("T")[0],
        venue: "",
        description: "",
      });
      setShowAdd(false);
      load();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to create event"));
    } finally {
      setSaving(false);
    }
  }

  function changeMonth(delta: number) {
    let m = viewMonth + delta;
    let y = viewYear;
    if (m < 0) {
      m = 11;
      y -= 1;
    } else if (m > 11) {
      m = 0;
      y += 1;
    }
    setViewMonth(m);
    setViewYear(y);
  }

  return (
    <PageShell
      title="Events"
      subtitle="School activities, exams, and important dates"
      action={
        <button type="button" className="btn btn-primary gw-btn-sm" onClick={() => setShowAdd((v) => !v)}>
          <Plus size={16} /> {showAdd ? "Cancel" : "Add event"}
        </button>
      }
    >
      {error && <div className="gw-alert gw-alert-error">{error}</div>}

      {showAdd && (
        <div className="gw-card gw-card-pad" style={{ marginBottom: 20 }}>
          <div className="gw-expense-form" style={{ gridTemplateColumns: "2fr 1fr 1fr auto" }}>
            <input
              className="form-input"
              placeholder="Event title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
            <input
              type="date"
              className="form-input"
              value={form.event_date}
              onChange={(e) => setForm({ ...form, event_date: e.target.value })}
            />
            <input
              className="form-input"
              placeholder="Venue"
              value={form.venue}
              onChange={(e) => setForm({ ...form, venue: e.target.value })}
            />
            <button type="button" className="btn btn-primary gw-btn-sm" onClick={addEvent} disabled={saving}>
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="gw-center">
          <div className="spinner" />
        </div>
      ) : (
        <>
          <div className="gw-pipeline" role="tablist" aria-label="Filter events">
            {FILTERS.map((f) => {
              const active = listFilter === f.key;
              return (
                <button
                  key={f.key}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  className={`gw-pipeline-stage${active ? " gw-pipeline-stage-active" : ""}`}
                  onClick={() => setListFilter(f.key)}
                >
                  <span className="gw-pipeline-count">{counts[f.key]}</span>
                  <span className="gw-pipeline-label">{f.label}</span>
                </button>
              );
            })}
          </div>

          <div className="events-layout">
          <div className="gw-card gw-card-pad events-calendar-card">
            <div className="events-calendar-head">
              <h3 className="gw-list-title">{monthLabel(viewYear, viewMonth)}</h3>
              <div className="events-calendar-nav">
                <button type="button" className="btn btn-ghost gw-btn-sm" onClick={() => changeMonth(-1)}>
                  ‹
                </button>
                <button type="button" className="btn btn-ghost gw-btn-sm" onClick={() => changeMonth(1)}>
                  ›
                </button>
              </div>
            </div>
            <div className="events-weekdays">
              {WEEKDAYS.map((d) => (
                <span key={d}>{d}</span>
              ))}
            </div>
            <div className="events-calendar-grid">
              {calendarCells.map((cell, i) =>
                cell ? (
                  <div
                    key={cell.iso}
                    className={`events-cal-day ${cell.iso === todayIso ? "today" : ""} ${
                      eventDates.has(cell.iso) ? "has-event" : ""
                    }`}
                  >
                    {cell.day}
                  </div>
                ) : (
                  <div key={`empty-${i}`} className="events-cal-day empty" />
                )
              )}
            </div>
          </div>

          <div className="gw-card gw-card-pad events-upcoming">
            <h3 className="gw-list-title" style={{ marginBottom: 16 }}>
              Upcoming
            </h3>
            {upcoming.length === 0 ? (
              <p className="gw-muted">No events scheduled.</p>
            ) : (
              <div className="events-upcoming-list">
                {upcoming.map((e) => {
                  const { month, day } = eventBadgeParts(e.event_date);
                  return (
                    <div key={e.id} className="events-upcoming-item">
                      <div className="events-upcoming-date">
                        <span className="events-upcoming-date-month">{month}</span>
                        <span className="events-upcoming-date-day">{day}</span>
                      </div>
                      <div className="events-upcoming-main">
                        <div className="events-upcoming-title">{e.title}</div>
                        <div className="gw-list-meta">
                          <CalendarDays size={12} style={{ display: "inline", marginRight: 4 }} />
                          {e.event_date}
                          {e.event_time ? ` · ${e.event_time}` : ""}
                        </div>
                        {e.venue && (
                          <div className="gw-list-meta">
                            <MapPin size={12} style={{ display: "inline", marginRight: 4 }} />
                            {e.venue}
                          </div>
                        )}
                      </div>
                      <StatusBadge tone="blue">Event</StatusBadge>
                    </div>
                  );
                })}
              </div>
            )}
            <Link href="/dashboard/notices" className="briefing-link" style={{ display: "inline-block", marginTop: 12 }}>
              Share as notice →
            </Link>
          </div>
        </div>
        </>
      )}
    </PageShell>
  );
}
