"use client";

// Same reasoning as MapCanvasLoader/RoutePlannerLoader: this reads
// localStorage, which doesn't exist during SSR, so it must never run
// server-side at all — not even behind suppressHydrationWarning.
import dynamic from "next/dynamic";

const ReporterIdentity = dynamic(() => import("./ReporterIdentity"), {
  ssr: false,
  loading: () => (
    <div className="h-[42px] w-full rounded-xl border border-dashed border-current/20 px-3.5 py-2.5 text-xs opacity-40">
      Demo: reporting as .
    </div>
  ),
});

export default function ReporterIdentityLoader() {
  return <ReporterIdentity />;
}
