// Presentational only — page.js fetches stats server-side and passes them
// in, so this component has no data-fetching or client-side concerns.

const ITEMS = [
  { key: "activeReports", label: "Active reports" },
  { key: "verifiedHotspots", label: "Verified hotspots" },
  { key: "trustContributors", label: "Trust score contributors" },
];

export default function StatStrip({ stats }) {
  return (
    <dl className="grid grid-cols-1 gap-8 border-t border-line-dark/50 pt-8 sm:grid-cols-3">
      {ITEMS.map(({ key, label }) => (
        <div key={key}>
          <dt className="font-mono text-xs uppercase tracking-[0.14em] opacity-60">
            {label}
          </dt>
          <dd className="mt-1 font-display text-4xl font-bold tabular-nums">
            {stats[key].toLocaleString()}
          </dd>
        </div>
      ))}
    </dl>
  );
}
