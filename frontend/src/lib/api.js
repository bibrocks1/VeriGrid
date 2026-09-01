// Thin API layer over the backend documented in the build guide. Every
// function tries the real endpoint first; if it's unreachable (no backend
// running, e.g. during frontend-only development or this demo build) it
// falls back to the matching fixture in mockData.js so the UI is always
// demoable. `source` on the return value tells callers which happened, which
// is what powers the "Demo mode" disclaimer in the footer.

import axios from "axios";
import {
  MOCK_REPORTS,
  MOCK_CLUSTERS,
  MOCK_STATS,
  MOCK_AUTHORITY_REPORT,
  MOCK_SYNC_LOG,
  MOCK_ROUTE,
} from "./mockData";
import { getDeviceId } from "./deviceId";
import { haversineMeters } from "./geo";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

const client = axios.create({
  baseURL: BASE_URL,
  // Generous: a report submission triggers a synchronous DBSCAN reclustering
  // pass with several sequential round trips to a remote (Neon) Postgres,
  // which can legitimately take several seconds — not a hang.
  timeout: 15000,
});

async function withFallback(request, fallbackData) {
  if (!BASE_URL) {
    return { data: fallbackData, source: "demo" };
  }
  try {
    const response = await request();
    return { data: response.data, source: "live" };
  } catch {
    return { data: fallbackData, source: "demo" };
  }
}

export function getReports() {
  return withFallback(() => client.get("/reports"), MOCK_REPORTS);
}

export function getClusters() {
  return withFallback(() => client.get("/clusters"), MOCK_CLUSTERS);
}

export function getStats() {
  return withFallback(() => client.get("/stats"), MOCK_STATS);
}

// Day 5: reports within `radiusM` of (lat, lng), closest first, each
// carrying `distanceM`. Demo-mode fallback computes the same thing against
// the mock fixtures with the same haversine math the backend uses server-
// side (PostGIS ST_Distance), so the UI behaves identically either way.
export function getNearbyReports({ lat, lng, radiusM = 500, category } = {}) {
  const params = { lat, lng, radius_m: radiusM };
  if (category) params.category = category;

  const fallback = MOCK_REPORTS.filter(
    (r) => !category || r.category === category,
  )
    .map((r) => ({ ...r, distanceM: haversineMeters(lat, lng, r.lat, r.lng) }))
    .filter((r) => r.distanceM <= radiusM)
    .sort((a, b) => a.distanceM - b.distanceM);

  return withFallback(
    () => client.get("/reports/nearby", { params }),
    fallback,
  );
}

export function createReport(payload) {
  const body = { ...payload, device_id: getDeviceId() };
  return withFallback(() => client.post("/reports", body), {
    ...payload,
    id: `demo-${Date.now()}`,
  });
}

export function sendChatMessage(payload) {
  return withFallback(() => client.post("/chat", payload), {
    role: "assistant",
    source: "verigrid",
    text: "Demo mode: connect NEXT_PUBLIC_API_URL to get live answers grounded in real reports and MirEye data.",
  });
}

export function getAuthorityReport(clusterId) {
  return withFallback(
    () => client.get(`/clusters/${clusterId}/report`),
    MOCK_AUTHORITY_REPORT,
  );
}

export function sendAuthorityReport(clusterId) {
  return withFallback(() => client.post(`/clusters/${clusterId}/send-report`), {
    ...MOCK_AUTHORITY_REPORT,
    status: "sent",
  });
}

export function getSyncStatus() {
  return withFallback(() => client.get("/mireye/sync-log"), MOCK_SYNC_LOG);
}

// Day 10: OSRM -> route geometry -> VeriGrid checks geometry against
// hazards -> safe route response (see backend/routing.py).
export function getSafeRoute({ originLat, originLng, destLat, destLng }) {
  const params = {
    origin_lat: originLat,
    origin_lng: originLng,
    dest_lat: destLat,
    dest_lng: destLng,
  };
  return withFallback(() => client.get("/route/safe", { params }), MOCK_ROUTE);
}
