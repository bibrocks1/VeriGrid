function formatRelativeTime(isoString) {
  const diffMs = Date.now() - new Date(isoString).getTime();
  const diffHours = Math.round(diffMs / (1000 * 60 * 60));
  if (diffHours < 1) return "under an hour ago";
  if (diffHours === 1) return "1 hour ago";
  return `${diffHours} hours ago`;
}

// Pulled from mireye_sync_log per the build guide — gives demo credibility
// that the MirEye integration is a real, live-syncing data source.
export default function SyncStatusBadge({ sync }) {
  const isOk = sync.status === "ok";

  return (
    <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-[0.1em]">
      <span
        className={`h-2 w-2 rounded-full ${isOk ? "bg-verified" : "bg-hazard"}`}
        aria-hidden
      />
      MirEye sync {isOk ? "ok" : "failed"} ·{" "}
      {formatRelativeTime(sync.lastSyncedAt)} ·{" "}
      {sync.recordsSynced.toLocaleString()} records
    </div>
  );
}
