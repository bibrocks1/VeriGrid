"use client";

import { useState } from "react";

// Shared by the chat panel and report form context: lets a user set a
// lat/lon either by typing it or by accepting the demo default, without
// depending on the live map instance.
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
        <label className="text-xs font-medium opacity-60">Lat</label>
        <input
          value={lat}
          onChange={(e) => setLat(e.target.value)}
          className="mt-1 block w-24 rounded-xl border border-line bg-transparent px-2.5 py-1.5 text-xs"
        />
      </div>
      <div>
        <label className="text-xs font-medium opacity-60">Lon</label>
        <input
          value={lng}
          onChange={(e) => setLng(e.target.value)}
          className="mt-1 block w-24 rounded-xl border border-line bg-transparent px-2.5 py-1.5 text-xs"
        />
      </div>
      <button
        type="button"
        onClick={apply}
        className="rounded-full border border-line px-3.5 py-1.5 text-xs font-medium opacity-70"
      >
        Set location
      </button>
    </div>
  );
}
