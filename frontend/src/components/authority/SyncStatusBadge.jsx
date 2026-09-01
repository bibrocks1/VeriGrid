function formatRelativeTime(isoString) {
  const diffMs = Date.now() - new Date(isoString).getTime();
  const diffHours = Math.round(diffMs / (1000 * 60 * 60));
  if (diffHours < 1) return "under an hour ago";
  if (diffHours === 1) return "1 hour ago";
  return `${diffHours} hours ago`;
}

// Pulled from mireye_sync_log per the build guide, gives demo credibility
// that the MirEye integration is a real, live-syncing data source.
export default function SyncStatusBadge({ sync }) {
  const isOk = sync.status === "ok";

  return (
    <div className="inline-flex items-center gap-2 rounded-full bg-card px-4 py-2.5 text-sm font-medium shadow-soft">
      <span
        className={`h-2 w-2 rounded-full ${isOk ? "bg-verified" : "bg-hazard"}`}
        aria-hidden
      />
      MirEye sync {isOk ? "ok" : "failed"} &middot;{" "}
      {sync.lastSyncedAt
        ? formatRelativeTime(sync.lastSyncedAt)
        : "no syncs yet"}{" "}
      &middot; {sync.recordsSynced.toLocaleString()} records
    </div>
  );
}
