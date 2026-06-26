"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Bell, Calendar, Search, Settings } from "lucide-react";
import { api } from "@/lib/api";
import { PersonMono } from "@/components/briefing/PersonMono";
import { roleLabel } from "@/lib/permissions";
import { GlobalSearch } from "./GlobalSearch";

type Notification = {
  id: string;
  title: string;
  body: string;
  is_read: boolean;
  created_at?: string;
  link?: string | null;
};

type Props = {
  userName: string;
  userRole: string;
  academicLabel: string;
  showSettings?: boolean;
};

function formatToday() {
  const d = new Date();
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${months[d.getMonth()]} ${d.getDate()}, ${days[d.getDay()]}`;
}

export function TopBar({ userName, userRole, academicLabel, showSettings = true }: Props) {
  const [searchOpen, setSearchOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const notifRef = useRef<HTMLDivElement>(null);

  const loadNotifications = useCallback(() => {
    api<{ data: { unread_count: number } }>("/api/v1/notifications/count")
      .then((r) => setUnread(r.data?.unread_count ?? 0))
      .catch(() => setUnread(0));
  }, []);

  const loadNotificationList = useCallback(() => {
    api<{ data: Notification[] }>("/api/v1/notifications")
      .then((r) => setNotifications(r.data || []))
      .catch(() => setNotifications([]));
  }, []);

  useEffect(() => {
    loadNotifications();
    const id = setInterval(loadNotifications, 60000);
    return () => clearInterval(id);
  }, [loadNotifications]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (!notifOpen) return;
    loadNotificationList();
    const onClick = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setNotifOpen(false);
      }
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [notifOpen, loadNotificationList]);

  async function markAllRead() {
    try {
      await api("/api/v1/notifications/read-all", { method: "POST" });
      setUnread(0);
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {
      /* ignore */
    }
  }

  return (
    <>
      <header className="header topbar">
        <span className="header-context topbar-context">{academicLabel}</span>

        <button
          type="button"
          className="topbar-search-trigger"
          onClick={() => setSearchOpen(true)}
        >
          <Search size={16} />
          <span className="topbar-search-placeholder">Search students, teachers, classes…</span>
          <kbd className="topbar-search-kbd">⌘K</kbd>
        </button>

        <div className="topbar-actions">
          <div className="topbar-notif-wrap" ref={notifRef}>
            <button
              type="button"
              className="topbar-icon-btn"
              aria-label="Notifications"
              onClick={() => setNotifOpen((v) => !v)}
            >
              <Bell size={20} />
              {unread > 0 && <span className="topbar-notif-badge" />}
            </button>
            {notifOpen && (
              <div className="topbar-notif-panel">
                <div className="topbar-notif-head">
                  <span className="topbar-notif-title">Notifications</span>
                  {unread > 0 && (
                    <button type="button" className="topbar-notif-mark" onClick={markAllRead}>
                      Mark all read
                    </button>
                  )}
                </div>
                <div className="topbar-notif-list">
                  {notifications.length === 0 ? (
                    <p className="topbar-notif-empty">No notifications yet</p>
                  ) : (
                    notifications.map((n) => (
                      <div
                        key={n.id}
                        className={`topbar-notif-item ${n.is_read ? "" : "unread"}`}
                      >
                        <div className="topbar-notif-item-title">{n.title}</div>
                        <div className="topbar-notif-item-body">{n.body}</div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {showSettings && (
            <Link href="/dashboard/settings" className="topbar-icon-btn" aria-label="Settings">
              <Settings size={20} />
            </Link>
          )}

          <div className="topbar-date-pill">
            <Calendar size={14} />
            <span>{formatToday()}</span>
          </div>

          <div className="header-user topbar-user">
            <div className="header-user-text">
              <div className="header-name">{userName}</div>
              <div className="header-role">{roleLabel(userRole)}</div>
            </div>
            <PersonMono name={userName} size={36} />
          </div>
        </div>
      </header>

      <GlobalSearch open={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
}
