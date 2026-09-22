import React from "react";
import ChatTab from "./ChatTab";

export default function ChatView({ isMobile }: { isMobile: boolean }) {
  return <ChatTab isMobile={isMobile} />;
}
