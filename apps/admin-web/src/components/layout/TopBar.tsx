"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Bell, Calendar, ChevronDown, CircleHelp, GraduationCap, LogOut, Search, Settings } from "lucide-react";
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
  onLogout: () => void | Promise<void>;
};

function formatToday() {
  const d = new Date();
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${months[d.getMonth()]} ${d.getDate()}, ${days[d.getDay()]}`;
}

export function TopBar({ userName, userRole, academicLabel, showSettings = true, onLogout }: Props) {
  const [searchOpen, setSearchOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const notifRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);

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
      if (e.key === "Escape") {
        setProfileOpen(false);
        setNotifOpen(false);
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

  useEffect(() => {
    if (!profileOpen) return;
    const onClick = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [profileOpen]);

  async function markAllRead() {
    try {
      await api("/api/v1/notifications/read-all", { method: "POST" });
      setUnread(0);
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {
      /* ignore */
    }
  }

  async function handleLogout() {
    setProfileOpen(false);
    await onLogout();
  }

  return (
    <>
      <header className="header topbar">
        <div className="topbar-left">
          <div className="topbar-chip topbar-chip--static topbar-context-chip">
            <GraduationCap size={14} aria-hidden />
            <span className="topbar-context">{academicLabel}</span>
          </div>
        </div>

        <div className="topbar-center">
          <button
            type="button"
            className="topbar-search-trigger"
            onClick={() => setSearchOpen(true)}
          >
            <Search size={16} />
            <span className="topbar-search-placeholder">Search students, teachers, classes…</span>
            <kbd className="topbar-search-kbd">⌘K</kbd>
          </button>
        </div>

        <div className="topbar-actions">
          <div className="topbar-notif-wrap" ref={notifRef}>
            <button
              type="button"
              className="topbar-chip topbar-chip--icon"
              aria-label="Notifications"
              onClick={() => {
                setProfileOpen(false);
                setNotifOpen((v) => !v);
              }}
            >
              <Bell size={18} />
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

          <div className="topbar-chip topbar-date-chip">
            <Calendar size={14} aria-hidden />
            <span>{formatToday()}</span>
          </div>

          <div className="topbar-profile-wrap" ref={profileRef}>
            <button
              type="button"
              className={`topbar-chip topbar-profile-chip topbar-profile-trigger${profileOpen ? " topbar-profile-trigger--open" : ""}`}
              onClick={() => {
                setNotifOpen(false);
                setProfileOpen((v) => !v);
              }}
              aria-expanded={profileOpen}
              aria-haspopup="menu"
              aria-label={`Account menu for ${userName}`}
            >
              <PersonMono name={userName} size={28} />
              <span className="topbar-profile-name">{userName}</span>
              <ChevronDown
                size={14}
                className={`topbar-profile-chevron${profileOpen ? " topbar-profile-chevron--open" : ""}`}
                aria-hidden
              />
            </button>

            {profileOpen && (
              <div className="topbar-profile-menu" role="menu">
                <div className="topbar-profile-menu-head">
                  <PersonMono name={userName} size={40} />
                  <div>
                    <div className="topbar-profile-menu-name">{userName}</div>
                    <div className="topbar-profile-menu-role">{roleLabel(userRole)}</div>
                  </div>
                </div>
                <div className="topbar-profile-menu-divider" />
                {showSettings && (
                  <Link
                    href="/dashboard/settings"
                    className="topbar-profile-item"
                    role="menuitem"
                    onClick={() => setProfileOpen(false)}
                  >
                    <Settings size={16} aria-hidden />
                    Settings
                  </Link>
                )}
                <a
                  href="mailto:hello@studynexs.com"
                  className="topbar-profile-item"
                  role="menuitem"
                  onClick={() => setProfileOpen(false)}
                >
                  <CircleHelp size={16} aria-hidden />
                  Help & support
                </a>
                <div className="topbar-profile-menu-divider" />
                <button
                  type="button"
                  className="topbar-profile-item topbar-profile-item--danger"
                  role="menuitem"
                  onClick={handleLogout}
                >
                  <LogOut size={16} aria-hidden />
                  Log out
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <GlobalSearch open={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
}
