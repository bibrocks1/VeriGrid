"use client";

// Same reasoning as MapCanvasLoader: RoutePlanner now renders a Leaflet map
// directly, and Leaflet touches `window` on import, so it must never run
// during SSR.
import dynamic from "next/dynamic";

const RoutePlanner = dynamic(() => import("./RoutePlanner"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[420px] w-full items-center justify-center rounded-3xl bg-card shadow-soft">
      <p className="text-sm opacity-50">Loading route planner.</p>
    </div>
  ),
});

export default function RoutePlannerLoader(props) {
  return <RoutePlanner {...props} />;
}
