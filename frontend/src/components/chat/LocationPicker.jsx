"use client";

import { useState } from "react";

// Shared by the chat panel, report form context, and (in a fuller build)
// the route planner — lets a user set a lat/lon either by typing it or by
// accepting the demo default, without depending on the live map instance.
export default function LocationPicker({ location, onChange }) {
  const [lat, setLat] = useState(String(location.lat));
  const [lng, setLng] = useState(String(location.lng));

  function apply() {
    const parsedLat = Number(lat);
    const parsedLng = Number(lng);
    if (!Number.isNaN(parsedLat) && !Number.isNaN(parsedLng)) {
      onChange({ lat: parsedLat, lng: parsedLng });
    }
  }

  return (
    <div className="flex flex-wrap items-end gap-2">
      <div>
        <label className="font-mono text-[0.65rem] uppercase tracking-[0.1em] opacity-60">
          Lat
        </label>
        <input
          value={lat}
          onChange={(e) => setLat(e.target.value)}
          className="mt-1 block w-24 rounded-sm border border-line bg-transparent px-2 py-1 font-mono text-xs"
        />
      </div>
      <div>
        <label className="font-mono text-[0.65rem] uppercase tracking-[0.1em] opacity-60">
          Lon
        </label>
        <input
          value={lng}
          onChange={(e) => setLng(e.target.value)}
          className="mt-1 block w-24 rounded-sm border border-line bg-transparent px-2 py-1 font-mono text-xs"
        />
      </div>
      <button
        type="button"
        onClick={apply}
        className="rounded-sm border border-line px-3 py-1.5 font-mono text-[0.65rem] uppercase tracking-[0.1em] opacity-70"
      >
        Set location
      </button>
    </div>
  );
}
