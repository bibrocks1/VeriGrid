// Small trust indicator for a reporter or cluster. Kept separate from
// ConfidenceMeter because trust (per-user reputation) and confidence
// (per-cluster consensus score) are distinct concepts in the scoring model.
export default function TrustBadge({ trust, size = "sm" }) {
  const textSize = size === "lg" ? "text-sm" : "text-xs";

  return (
    <span
      className={`inline-flex items-center gap-1.5 ${textSize} font-medium tabular-nums opacity-80`}
      title="Reporter trust score"
    >
      <span className="h-1.5 w-1.5 rounded-full bg-verified" aria-hidden />
      Trust {trust}
    </span>
  );
}
