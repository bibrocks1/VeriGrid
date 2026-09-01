import { CONFIDENCE_THRESHOLDS } from "@/lib/constants";

const STATUS_COLOR = {
  candidate: "var(--color-amber)",
  verified: "var(--color-verified)",
};

// Visual bar + status badge for a cluster's confidence score. Thresholds
// are imported from lib/constants so this always reflects the backend's
// actual scoring rules (candidate >= 25, verified >= 60) rather than a
// hardcoded copy.
export default function ConfidenceMeter({ confidence, status }) {
  const color = STATUS_COLOR[status] ?? "var(--color-muted)";

  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <span
          className="badge capitalize"
          style={{ backgroundColor: `${color}22`, color }}
        >
          {status}
        </span>
        <span className="text-sm tabular-nums opacity-70">
          {confidence}/100
        </span>
      </div>
      <div className="relative mt-3 h-2 w-full overflow-hidden rounded-full bg-current/10">
        <div
          className="h-full rounded-full transition-[width]"
          style={{
            width: `${Math.min(confidence, 100)}%`,
            backgroundColor: color,
          }}
        />
        <div
          className="absolute top-0 h-full w-px bg-current/30"
          style={{ left: `${CONFIDENCE_THRESHOLDS.candidate}%` }}
          title={`Candidate threshold: ${CONFIDENCE_THRESHOLDS.candidate}`}
        />
        <div
          className="absolute top-0 h-full w-px bg-current/30"
          style={{ left: `${CONFIDENCE_THRESHOLDS.verified}%` }}
          title={`Verified threshold: ${CONFIDENCE_THRESHOLDS.verified}`}
        />
      </div>
    </div>
  );
}
