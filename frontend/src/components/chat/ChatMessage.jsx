const SOURCE_LABEL = {
  mireye: "MirEye infrastructure data",
  verigrid: "VeriGrid citizen reports",
};

const SOURCE_COLOR = {
  mireye: "text-amber",
  verigrid: "text-verified",
};

// Bubble with explicit source attribution: the build guide (Day 9) calls
// out that MirEye-sourced and citizen-reported answers must be visually
// distinguishable, not just textually noted.
export default function ChatMessage({ role, source, text }) {
  const isUser = role === "user";

  return (
    <div className={`flex flex-col gap-1 ${isUser ? "items-end" : "items-start"}`}>
      {source && (
        <span className={`text-xs font-semibold ${SOURCE_COLOR[source]}`}>{SOURCE_LABEL[source]}</span>
      )}
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isUser ? "bg-ink text-ink-text" : "bg-card-soft text-paper-text"
        }`}
      >
        {text}
      </div>
    </div>
  );
}
