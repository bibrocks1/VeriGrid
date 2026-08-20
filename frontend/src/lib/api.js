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
} from "./mockData";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 4000,
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

export function createReport(payload) {
  return withFallback(() => client.post("/reports", payload), {
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
