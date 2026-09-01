"use client";

import { useState } from "react";
import { getDeviceId, resetDeviceId } from "@/lib/deviceId";

// Loaded with ssr:false (see ReporterIdentityLoader) — never runs on the
// server, so there's no "server" placeholder to flash and no hydration
// mismatch to suppress; its very first client render already has the
// real localStorage-backed id.
export default function ReporterIdentity() {
  const [deviceId, setDeviceId] = useState(() => getDeviceId());

  return (
    <div className="flex items-center justify-between gap-3 rounded-xl border border-dashed border-current/20 px-3.5 py-2.5 text-xs opacity-70">
      <span>
        Demo: reporting as <span className="font-mono">{deviceId.slice(0, 8)}</span>
      </span>
      <button
        type="button"
        onClick={() => setDeviceId(resetDeviceId())}
        className="shrink-0 rounded-full border border-current/20 px-3 py-1 font-medium hover:opacity-80"
      >
        Simulate new reporter
      </button>
    </div>
  );
}
