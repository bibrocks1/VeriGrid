"use client";

import { useEffect, useState } from "react";
import { getNearbyReports } from "@/lib/api";
import { formatDistance } from "@/lib/geo";
import { CATEGORIES } from "@/lib/constants";

// Shown above the report form when a point is clicked, so a reporter can
// see what's already been filed nearby before adding a new report.
const NEARBY_RADIUS_M = 500;
const MAX_SHOWN = 4;

const CATEGORY_LABEL = Object.fromEntries(
  CATEGORIES.map((c) => [c.id, c.label]),
);

export default function NearbyReportsList({ lat, lng }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getNearbyReports({ lat, lng, radiusM: NEARBY_RADIUS_M }).then(
      ({ data }) => {
        if (!cancelled) {
          setReports(data);
          setLoading(false);
        }
      },
    );
    return () => {
      cancelled = true;
    };
  }, [lat, lng]);

  if (loading) {
    return (
      <p className="mb-4 text-sm opacity-50">Checking for nearby reports.</p>
    );
  }

  if (reports.length === 0) {
    return (
      <p className="mb-4 text-sm opacity-60">
        No reports within {NEARBY_RADIUS_M}m of this point yet. You&apos;d be
        the first.
      </p>
    );
  }

  return (
    <div className="mb-4 flex flex-col gap-2 border-b border-current/15 pb-4">
      <p className="text-sm font-medium opacity-70">
        {reports.length} report{reports.length === 1 ? "" : "s"} already nearby
      </p>
      <ul className="flex flex-col gap-2">
        {reports.slice(0, MAX_SHOWN).map((r) => (
          <li key={r.id} className="rounded-xl bg-current/5 p-3 text-sm">
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium capitalize opacity-80">
                {CATEGORY_LABEL[r.category] ?? r.category}
              </span>
              <span className="opacity-50">{formatDistance(r.distanceM)}</span>
            </div>
            {r.description && (
              <p className="mt-1 opacity-70">{r.description}</p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
