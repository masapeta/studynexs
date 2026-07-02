"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  BookOpen,
  CalendarCheck,
  Plus,
  UserPlus,
  Wallet,
} from "lucide-react";
import { api } from "@/lib/api";
import { eventBadgeParts } from "@/lib/format";
import { StatusBadge } from "./StatusBadge";

type ActivityItem = {
  icon: React.ElementType;
  text: string;
  time: string;
  tone?: "sage" | "brass" | "blue" | "coral";
};

type EventItem = {
  id: string;
  title: string;
  event_date: string;
  event_time?: string | null;
  venue?: string | null;
};

type TodoItem = {
  text: string;
  done: boolean;
  priority: "low" | "medium" | "high";
};

type Props = {
  userId: string;
  isAdmin: boolean;
  layout?: "default" | "executive";
};

function relativeTime(iso?: string) {
  if (!iso) return "Recently";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const mins = Math.floor((Date.now() - d.getTime()) / 60000);
  if (mins < 60) return `${Math.max(1, mins)} min ago`;
  if (mins < 1440) return `${Math.floor(mins / 60)} hour${mins >= 120 ? "s" : ""} ago`;
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

function loadTodos(userId: string): TodoItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(`academix-todos-${userId}`);
    if (raw) return JSON.parse(raw) as TodoItem[];
  } catch {
    /* ignore */
  }
  return [
    { text: "Review pending tuition payments", done: false, priority: "high" },
    { text: "Reply to parent messages", done: false, priority: "high" },
    { text: "Confirm upcoming event venues", done: false, priority: "medium" },
    { text: "Review exam schedule", done: false, priority: "medium" },
  ];
}

function saveTodos(userId: string, items: TodoItem[]) {
  localStorage.setItem(`academix-todos-${userId}`, JSON.stringify(items));
}

function isThisWeek(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return false;
  const now = new Date();
  const start = new Date(now);
  start.setDate(now.getDate() - now.getDay());
  start.setHours(0, 0, 0, 0);
  const end = new Date(start);
  end.setDate(start.getDate() + 7);
  return d >= start && d < end;
}

export function DashboardWidgets({ userId, isAdmin, layout = "default" }: Props) {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [weekEvents, setWeekEvents] = useState<EventItem[]>([]);
  const [todos, setTodos] = useState<TodoItem[]>([]);
  const [newTodo, setNewTodo] = useState("");

  const persistTodos = useCallback(
    (items: TodoItem[]) => {
      setTodos(items);
      saveTodos(userId, items);
    },
    [userId]
  );

  useEffect(() => {
    setTodos(loadTodos(userId));
  }, [userId]);

  useEffect(() => {
    const items: ActivityItem[] = [];

    Promise.all([
      api<{ data: { title: string; body: string; created_at?: string }[] }>(
        "/api/v1/notifications?unread_only=false"
      ).catch(() => ({ data: [] })),
      isAdmin
        ? api<{ data: { student_name?: string; amount_paid?: number; paid_at?: string }[] }>(
            "/api/v1/fees/recent?limit=3"
          ).catch(() => ({ data: [] }))
        : Promise.resolve({ data: [] }),
      api<{ data: { title: string; created_at?: string }[] }>("/api/v1/notices").catch(
        () => ({ data: [] })
      ),
    ]).then(([notifs, fees, notices]) => {
      (notifs.data || []).slice(0, 3).forEach((n) => {
        items.push({
          icon: CalendarCheck,
          text: n.title,
          time: relativeTime(n.created_at),
          tone: "blue",
        });
      });
      (fees.data || []).forEach((f) => {
        items.push({
          icon: Wallet,
          text: `Tuition payment${f.student_name ? ` from ${f.student_name}` : ""}${
            f.amount_paid ? ` · ₹${f.amount_paid.toLocaleString()}` : ""
          }`,
          time: relativeTime(f.paid_at),
          tone: "sage",
        });
      });
      (notices.data || []).slice(0, 2).forEach((n) => {
        items.push({
          icon: UserPlus,
          text: `Notice: ${n.title}`,
          time: relativeTime(n.created_at),
          tone: "brass",
        });
      });
      if (items.length === 0) {
        items.push({
          icon: BookOpen,
          text: "No recent activity — your school day is quiet so far.",
          time: "Today",
          tone: "blue",
        });
      }
      setActivities(items.slice(0, 6));
    });

    api<{ data: EventItem[] }>("/api/v1/ops/events")
      .then((r) => {
        const sorted = [...(r.data || [])].sort(
          (a, b) => new Date(a.event_date).getTime() - new Date(b.event_date).getTime()
        );
        const week = sorted.filter((e) => isThisWeek(e.event_date)).slice(0, 4);
        setWeekEvents(week.length ? week : sorted.slice(0, 4));
      })
      .catch(() => setWeekEvents([]));
  }, [isAdmin]);

  function toggleTodo(idx: number) {
    const next = todos.map((t, i) => (i === idx ? { ...t, done: !t.done } : t));
    persistTodos(next);
  }

  function addTodo() {
    const text = newTodo.trim();
    if (!text) return;
    persistTodos([{ text, done: false, priority: "medium" }, ...todos]);
    setNewTodo("");
  }

  const gridClass =
    layout === "executive"
      ? "dashboard-widgets-grid dashboard-widgets-grid--executive"
      : "dashboard-widgets-grid";

  const chipPanel = layout === "executive" ? "briefing-glass-chip briefing-card briefing-panel" : "briefing-card briefing-panel";

  const activityPanel = (
    <div className={chipPanel}>
      <div className="briefing-panel-head">
        <h3>Recent activity</h3>
        <Link href="/dashboard/notices" className="briefing-link briefing-panel-action">
          View all
        </Link>
      </div>
      <div className="dashboard-activity-list">
        {activities.map((a, i) => {
          const Icon = a.icon;
          return (
            <div key={i} className="dashboard-activity-row">
              <div className={`dashboard-activity-icon tone-${a.tone || "blue"}`}>
                <Icon size={15} />
              </div>
              <div>
                <div className="dashboard-activity-text">{a.text}</div>
                <div className="dashboard-activity-time">{a.time}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  const eventsPanel = (
    <div className={chipPanel}>
      <div className="briefing-panel-head">
        <h3>This week</h3>
        <Link href="/dashboard/events" className="briefing-link briefing-panel-action">
          All events
        </Link>
      </div>
      <div className="dashboard-events-list">
        {weekEvents.length === 0 ? (
          <p className="briefing-muted-text">No events scheduled this week.</p>
        ) : (
          weekEvents.map((e) => {
            const { month, day } = eventBadgeParts(e.event_date);
            return (
              <div key={e.id} className="dashboard-event-row">
                <div className="dashboard-event-date">
                  <span className="dashboard-event-month">{month}</span>
                  <span className="dashboard-event-day">{day}</span>
                </div>
                <div>
                  <div className="dashboard-event-title">{e.title}</div>
                  <div className="dashboard-event-meta">
                    {e.event_time || "All day"}
                    {e.venue ? ` · ${e.venue}` : ""}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );

  const todoPanel = (
    <div className={`${chipPanel} briefing-exec-todo`}>
      <div className="briefing-panel-head">
        <h3>To-do list</h3>
      </div>
      <div className="dashboard-todo-list">
        {todos.map((t, i) => (
          <label key={i} className="dashboard-todo-row">
            <input type="checkbox" checked={t.done} onChange={() => toggleTodo(i)} />
            <span className={t.done ? "done" : ""}>{t.text}</span>
            {t.priority === "high" && !t.done && (
              <StatusBadge tone="red">Urgent</StatusBadge>
            )}
          </label>
        ))}
      </div>
      <div className="dashboard-todo-add">
        <input
          className="form-input"
          placeholder="Add a task…"
          value={newTodo}
          onChange={(e) => setNewTodo(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addTodo()}
        />
        <button type="button" className="btn btn-ghost gw-btn-sm" onClick={addTodo}>
          <Plus size={14} /> Add
        </button>
      </div>
    </div>
  );

  if (layout === "executive") {
    return (
      <div className="briefing-exec-row briefing-exec-row--ops">
        {activityPanel}
        {eventsPanel}
        {todoPanel}
      </div>
    );
  }

  return (
    <div className={gridClass}>
      {activityPanel}
      {eventsPanel}
      {todoPanel}
    </div>
  );
}
