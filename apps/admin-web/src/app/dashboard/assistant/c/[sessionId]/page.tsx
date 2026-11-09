"use client";

import { useParams } from "next/navigation";
import { ChatPage } from "@/components/assistant/ChatPage";

export default function DashboardConversationPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  return <ChatPage sessionId={sessionId} />;
}
