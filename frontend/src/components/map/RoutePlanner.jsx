"use client";

import { useState } from "react";

// Demo route planner (README Hero 6 / Day 10). Renders a schematic route —
// not a live OSRM call — so the detour-around-a-hazard behavior is legible
// without depending on a running routing backend. Swap `planRoute` for a
// real OSRM request once that service exists.
function planRoute(origin, destination) {
  const hasHazard = Boolean(origin.trim() && destination.trim());
  return {
    distanceKm: 4.2,
    durationMin: 14,
    detoured: hasHazard,
    avoided: hasHazard
      ? { category: "waterlogging", description: "Ward 4 market underpass" }
      : null,
  };
}

export default function RoutePlanner() {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [route, setRoute] = useState(null);

  function handleSubmit(event) {
    event.preventDefault();
    setRoute(planRoute(origin, destination));
  }

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label className="font-mono text-xs uppercase tracking-[0.1em] opacity-70">
            From
          </label>
          <input
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
            placeholder="Ward 4 Market Gate"
            className="mt-1.5 w-full rounded-sm border border-line bg-transparent px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="font-mono text-xs uppercase tracking-[0.1em] opacity-70">
            To
          </label>
          <input
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="Cross Street 9"
            className="mt-1.5 w-full rounded-sm border border-line bg-transparent px-3 py-2 text-sm"
          />
        </div>
        <button
          type="submit"
          className="w-fit rounded-sm bg-ink px-4 py-2 font-mono text-xs uppercase tracking-[0.1em] text-ink-text transition-opacity hover:opacity-90"
        >
          Plan safe route
        </button>
      </form>

      <div className="rounded-sm border border-line bg-paper-2/50 p-6">
        {!route ? (
          <p className="text-sm opacity-60">
            Enter a start and end point to see a route that avoids verified
            hotspots along the way.
          </p>
        ) : (
          <div className="flex flex-col gap-4">
            <svg viewBox="0 0 320 90" className="w-full" aria-hidden>
              <path
                d="M10,70 C 90,10 130,80 190,30 S 300,20 310,20"
                fill="none"
                stroke="currentColor"
                strokeOpacity="0.5"
                strokeWidth="2"
                strokeDasharray={route.detoured ? "0" : "4 4"}
              />
              <circle cx="10" cy="70" r="5" fill="var(--color-verified)" />
              <circle cx="310" cy="20" r="5" fill="var(--color-hazard)" />
              {route.detoured && (
                <circle
                  cx="150"
                  cy="55"
                  r="6"
                  fill="var(--color-amber)"
                  fillOpacity="0.4"
                  stroke="var(--color-amber)"
                  strokeWidth="1.5"
                />
              )}
            </svg>

            <dl className="grid grid-cols-2 gap-3 font-mono text-xs">
              <div>
                <dt className="opacity-50">Distance</dt>
                <dd className="mt-1">{route.distanceKm} km</dd>
              </div>
              <div>
                <dt className="opacity-50">Duration</dt>
                <dd className="mt-1">{route.durationMin} min</dd>
              </div>
            </dl>

            {route.avoided && (
              <p className="stamp w-fit text-amber">
                Detoured around {route.avoided.description}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
