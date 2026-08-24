import L from "leaflet";

// Custom divIcons built from plain HTML/CSS instead of Leaflet's default
// marker images. This sidesteps the classic Next.js + Leaflet broken-marker-
// asset problem entirely (no image files to resolve).

const CATEGORY_COLOR = {
  flooding: "#3178c6",
  waterlogging: "#3178c6",
  road_damage: "#c1442e",
  construction: "#d98a2b",
  safety: "#c1442e",
  environmental: "#2f8f5b",
  traffic: "#8b8b8b",
  other: "#8b8b8b",
};

export function reportIcon(category) {
  const color = CATEGORY_COLOR[category] ?? "#8b8b8b";
  return L.divIcon({
    className: "",
    html: `<span style="
      display:block;width:12px;height:12px;border-radius:50%;
      background:${color};border:2px solid rgba(11,11,12,0.85);
      box-shadow:0 0 0 2px rgba(255,255,255,0.7);
    "></span>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });
}

const STATUS_COLOR = {
  candidate: "#d98a2b",
  verified: "#2f8f5b",
};

export function clusterIcon(status, reporterCount) {
  const color = STATUS_COLOR[status] ?? "#8b8b8b";
  const size = Math.min(22 + reporterCount * 2, 44);
  return L.divIcon({
    className: "",
    html: `<span style="
      display:flex;align-items:center;justify-content:center;
      width:${size}px;height:${size}px;border-radius:50%;
      background:${color};color:#fff;
      box-shadow:0 2px 8px rgba(0,0,0,0.25);
      font:600 11px system-ui, sans-serif;
    ">${reporterCount}</span>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}
