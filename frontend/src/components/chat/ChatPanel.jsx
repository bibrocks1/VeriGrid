"use client";

import { useState } from "react";
import ChatMessage from "./ChatMessage";
import LocationPicker from "./LocationPicker";
import { sendChatMessage } from "@/lib/api";
import { MOCK_CENTER, MOCK_CHAT_HISTORY } from "@/lib/mockData";

// Follow-up support is intentionally shallow: only the last two turns are
// sent as context, matching Day 9's requirement, rather than the full
// history (which would make answers drift from the location in question).
const CONTEXT_TURNS = 2;

export default function ChatPanel() {
  const [location, setLocation] = useState(MOCK_CENTER);
  const [messages, setMessages] = useState(MOCK_CHAT_HISTORY);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  async function handleSend(event) {
    event.preventDefault();
    const text = input.trim();
    if (!text || sending) return;

    const userMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      source: null,
      text,
    };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput("");
    setSending(true);

    const { data } = await sendChatMessage({
      message: text,
      location,
      context: nextMessages.slice(-1 - CONTEXT_TURNS * 2),
    });

    setMessages((current) => [
      ...current,
      {
        id: `a-${Date.now()}`,
        role: "assistant",
        source: data.source ?? "verigrid",
        text: data.text,
      },
    ]);
    setSending(false);
  }

  return (
    <div className="flex flex-col gap-4 rounded-sm border border-line bg-paper-2/40 p-5 sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-4">
        <span className="font-mono text-xs uppercase tracking-[0.1em] opacity-60">
          Asking about
        </span>
        <LocationPicker location={location} onChange={setLocation} />
      </div>

      <div className="flex max-h-80 flex-col gap-4 overflow-y-auto py-2">
        {messages.map((m) => (
          <ChatMessage
            key={m.id}
            role={m.role}
            source={m.source}
            text={m.text}
          />
        ))}
        {sending && (
          <p className="font-mono text-xs opacity-50">
            VeriGrid is checking sources…
          </p>
        )}
      </div>

      <form
        onSubmit={handleSend}
        className="flex gap-2 border-t border-line pt-4"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Is it safe to walk near the canal right now?"
          className="flex-1 rounded-sm border border-line bg-transparent px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={sending}
          className="rounded-sm bg-ink px-4 py-2 font-mono text-xs uppercase tracking-[0.1em] text-ink-text disabled:opacity-50"
        >
          Ask
        </button>
      </form>
    </div>
  );
}
