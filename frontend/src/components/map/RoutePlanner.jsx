"use client";

import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
} from "react-leaflet";
import LocationPicker from "@/components/chat/LocationPicker";
import { getSafeRoute } from "@/lib/api";
import { MOCK_CENTER } from "@/lib/mockData";

const DEFAULT_ORIGIN = MOCK_CENTER;
const DEFAULT_DESTINATION = { lat: 29.767, lng: -95.3775 };

function dotIcon(color) {
  return L.divIcon({
    className: "",
    html: `<span style="
      display:block;width:14px;height:14px;border-radius:50%;
      background:${color};border:2px solid rgba(11,11,12,0.85);
      box-shadow:0 0 0 2px rgba(255,255,255,0.7);
    "></span>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

const originIcon = dotIcon("#2f8f5b");
const destinationIcon = dotIcon("#c1442e");
const hazardIcon = L.divIcon({
  className: "",
  html: `<span style="
    display:flex;align-items:center;justify-content:center;
    width:22px;height:22px;border-radius:50%;
    background:#d98a2b;color:#fff;font:700 12px system-ui, sans-serif;
    box-shadow:0 2px 8px rgba(0,0,0,0.3);
  ">!</span>`,
  iconSize: [22, 22],
  iconAnchor: [11, 11],
});

function metersToMiles(m) {
  return (m / 1609.34).toFixed(1);
}

function secondsToMinutes(s) {
  return Math.round(s / 60);
}

// Real hazard-aware routing: OSRM supplies the route geometry, the backend
// checks that geometry against verified clusters, and this component draws
// the result — a polyline plus any hazard warnings along the way. Origin/
// destination are set by coordinate (LocationPicker) rather than free-text
// address search, since there's no geocoder wired up.
export default function RoutePlanner() {
  const [origin, setOrigin] = useState(DEFAULT_ORIGIN);
  const [destination, setDestination] = useState(DEFAULT_DESTINATION);
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showSteps, setShowSteps] = useState(false);

  async function planRoute(event) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    const { data, source } = await getSafeRoute({
      originLat: origin.lat,
      originLng: origin.lng,
      destLat: destination.lat,
      destLng: destination.lng,
    });
    if (source === "demo" && !data.geometry) {
      setError("Couldn't reach the routing service.");
      setRoute(null);
    } else {
      setRoute(data);
    }
    setLoading(false);
  }

  return (
    <div className="grid grid-cols-1 gap-6 rounded-3xl bg-card p-6 shadow-soft sm:p-8 lg:grid-cols-2">
      <div className="flex flex-col gap-4">
        <div>
          <p className="text-xs font-medium opacity-60">From</p>
          <div className="mt-1.5">
            <LocationPicker location={origin} onChange={setOrigin} />
          </div>
        </div>
        <div>
          <p className="text-xs font-medium opacity-60">To</p>
          <div className="mt-1.5">
            <LocationPicker location={destination} onChange={setDestination} />
          </div>
        </div>
        <button
          type="button"
          onClick={planRoute}
          disabled={loading}
          className="w-fit rounded-full bg-ink px-5 py-2.5 text-sm font-semibold text-ink-text transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "Planning." : "Plan safe route"}
        </button>

        {route && (
          <>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="opacity-50">Distance</dt>
                <dd className="mt-1">{metersToMiles(route.distanceM)} mi</dd>
              </div>
              <div>
                <dt className="opacity-50">Duration</dt>
                <dd className="mt-1">
                  {secondsToMinutes(route.durationS)} min
                </dd>
              </div>
            </dl>

            {route.hazardWarnings.length > 0 ? (
              <div className="flex flex-col gap-2">
                {route.hazardWarnings.map((w) => (
                  <p
                    key={w.clusterId}
                    className="badge w-fit bg-amber/15 text-amber"
                  >
                    Passes ~{Math.round(w.distanceM)}m from a verified{" "}
                    {w.category.replace("_", " ")} hotspot
                  </p>
                ))}
              </div>
            ) : (
              <p className="badge w-fit bg-verified/15 text-verified">
                No verified hazards along this route
              </p>
            )}

            {route.steps?.length > 0 && (
              <div>
                <button
                  type="button"
                  onClick={() => setShowSteps((v) => !v)}
                  className="text-xs font-semibold underline decoration-line underline-offset-4"
                >
                  {showSteps ? "Hide" : "Show"} turn-by-turn directions
                </button>
                {showSteps && (
                  <ol className="mt-3 flex flex-col gap-2 text-sm opacity-80">
                    {route.steps.map((step, i) => (
                      <li key={i}>
                        {i + 1}. {step.instruction} (
                        {Math.round(step.distanceM)}m)
                      </li>
                    ))}
                  </ol>
                )}
              </div>
            )}
          </>
        )}

        {error && <p className="text-sm text-hazard">{error}</p>}
      </div>

      <div className="h-90 w-full overflow-hidden rounded-2xl lg:h-full">
        <MapContainer
          center={[origin.lat, origin.lng]}
          zoom={13}
          scrollWheelZoom={false}
          className="h-full w-full"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={[origin.lat, origin.lng]} icon={originIcon} />
          <Marker
            position={[destination.lat, destination.lng]}
            icon={destinationIcon}
          />

          {route?.geometry && (
            <Polyline
              positions={route.geometry}
              pathOptions={{ color: "#0b0b0c", weight: 4, opacity: 0.7 }}
            />
          )}

          {route?.hazardWarnings.map((w) => (
            <Marker
              key={w.clusterId}
              position={[w.lat, w.lng]}
              icon={hazardIcon}
            >
              <Popup>
                <p className="text-xs font-semibold capitalize">
                  {w.category.replace("_", " ")} hotspot
                </p>
                <p className="mt-1 text-xs opacity-70">
                  {Math.round(w.distanceM)}m from route &middot; confidence{" "}
                  {w.confidence}/100
                </p>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}
