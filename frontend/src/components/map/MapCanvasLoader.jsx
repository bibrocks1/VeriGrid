"use client";

// Leaflet touches `window` on import, so MapCanvas must never run during SSR.
// `ssr: false` on next/dynamic is only allowed inside a Client Component
// (see node_modules/next/dist/docs/01-app/02-guides/lazy-loading.md), hence
// this thin wrapper instead of dynamic-importing directly from page.js.
import dynamic from "next/dynamic";

const MapCanvas = dynamic(() => import("./MapCanvas"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[520px] w-full items-center justify-center rounded-sm border border-line-dark/60 bg-ink-2/40">
      <p className="font-mono text-xs uppercase tracking-[0.1em] text-ink-text/50">
        Loading map…
      </p>
    </div>
  ),
});

export default function MapCanvasLoader(props) {
  return <MapCanvas {...props} />;
}
