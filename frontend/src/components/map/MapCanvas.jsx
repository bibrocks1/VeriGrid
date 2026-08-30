"use client";

import "leaflet/dist/leaflet.css";
import { useMemo, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMapEvents,
} from "react-leaflet";
import { reportIcon, clusterIcon } from "./markerIcons";
import MapLayerToggle from "./MapLayerToggle";
import CategoryFilterChips from "./CategoryFilterChips";
import ReportForm from "@/components/report/ReportForm";
import ReportConfirmation from "@/components/report/ReportConfirmation";
import NearbyReportsList from "./NearbyReportsList";
import { MOCK_CENTER } from "@/lib/mockData";

function ClickToReport({ onPick }) {
  useMapEvents({
    click(e) {
      onPick({ lat: e.latlng.lat, lng: e.latlng.lng });
    },
  });
  return null;
}

// The core product surface: interactive map with layer + category filters,
// click-to-report, and marker popups for both raw reports and clusters.
// Owns its own layer/filter/draft-report state since all of it is local
// interaction that doesn't need to live above this component.
export default function MapCanvas({ reports, clusters }) {
  const [activeLayers, setActiveLayers] = useState([
    "raw",
    "candidate",
    "verified",
  ]);
  const [activeCategories, setActiveCategories] = useState(() =>
    Array.from(
      new Set(
        reports.map((r) => r.category).concat(clusters.map((c) => c.category)),
      ),
    ),
  );
  const [draftLocation, setDraftLocation] = useState(null);
  const [confirmedReport, setConfirmedReport] = useState(null);
  const [localReports, setLocalReports] = useState(reports);

  function toggleLayer(id) {
    setActiveLayers((current) =>
      current.includes(id) ? current.filter((l) => l !== id) : [...current, id],
    );
  }

  function toggleCategory(id) {
    setActiveCategories((current) =>
      current.includes(id) ? current.filter((c) => c !== id) : [...current, id],
    );
  }

  const visibleReports = useMemo(
    () =>
      activeLayers.includes("raw")
        ? localReports.filter((r) => activeCategories.includes(r.category))
        : [],
    [localReports, activeLayers, activeCategories],
  );

  const visibleClusters = useMemo(
    () =>
      clusters.filter(
        (c) =>
          activeLayers.includes(c.status) &&
          activeCategories.includes(c.category),
      ),
    [clusters, activeLayers, activeCategories],
  );

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <MapLayerToggle activeLayers={activeLayers} onToggle={toggleLayer} />
        <CategoryFilterChips
          activeCategories={activeCategories}
          onToggle={toggleCategory}
        />
      </div>

      <div className="relative isolate h-[520px] w-full overflow-hidden rounded-2xl">
        <MapContainer
          center={MOCK_CENTER}
          zoom={14}
          scrollWheelZoom={false}
          className="h-full w-full"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <ClickToReport onPick={setDraftLocation} />

          {visibleReports.map((report) => (
            <Marker
              key={report.id}
              position={[report.lat, report.lng]}
              icon={reportIcon(report.category)}
            >
              <Popup>
                <p className="text-xs font-semibold capitalize">
                  {report.category.replace("_", " ")}
                </p>
                <p className="mt-1 text-sm">{report.description}</p>
              </Popup>
            </Marker>
          ))}

          {visibleClusters.map((cluster) => (
            <Marker
              key={cluster.id}
              position={[cluster.lat, cluster.lng]}
              icon={clusterIcon(cluster.status, cluster.reporterCount)}
            >
              <Popup>
                <p className="text-xs font-semibold capitalize">
                  {cluster.category.replace("_", " ")} &middot; {cluster.status}
                </p>
                <p className="mt-1 text-sm">{cluster.description}</p>
                <p className="mt-2 text-xs opacity-70">
                  Confidence {cluster.confidence}/100 &middot; Verified by{" "}
                  {cluster.distinctReporters} independent reporters
                </p>
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        {draftLocation && (
          <div className="absolute inset-y-0 right-0 z-[1000] w-full max-w-sm overflow-y-auto rounded-r-2xl bg-ink-card/95 p-5 text-ink-text backdrop-blur">
            {confirmedReport ? (
              <ReportConfirmation
                report={confirmedReport}
                onReset={() => {
                  setDraftLocation(null);
                  setConfirmedReport(null);
                }}
              />
            ) : (
              <>
                <p className="mb-4 text-sm font-semibold">
                  New report at this point
                </p>
                <NearbyReportsList
                  key={`${draftLocation.lat}-${draftLocation.lng}`}
                  lat={draftLocation.lat}
                  lng={draftLocation.lng}
                />
                <ReportForm
                  location={draftLocation}
                  onCancel={() => setDraftLocation(null)}
                  onSubmitted={(report) => {
                    setLocalReports((current) => [
                      ...current,
                      { ...report, id: report.id ?? `local-${Date.now()}` },
                    ]);
                    setConfirmedReport(report);
                  }}
                />
              </>
            )}
          </div>
        )}
      </div>

      <p className="text-sm text-ink-text/50">
        Click anywhere on the map to file a report at that location.
      </p>
    </div>
  );
}
