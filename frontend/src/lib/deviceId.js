// Identifies an anonymous browser as "the same reporter" across visits, so
// the backend's consensus engine can dedupe contributors by user without a
// login system. SSR-safe: falls back to a throwaway id on the server, where
// localStorage doesn't exist and no report submission ever actually happens.
const STORAGE_KEY = "verigrid_device_id";

export function getDeviceId() {
  if (typeof window === "undefined") {
    return "server";
  }

  const existing = window.localStorage.getItem(STORAGE_KEY);
  if (existing) {
    return existing;
  }

  const id = crypto.randomUUID();
  window.localStorage.setItem(STORAGE_KEY, id);
  return id;
}
