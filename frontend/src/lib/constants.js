// Shared vocabulary for the whole app. Keep category/status definitions here
// so every component (map, form, filters, cards) stays in sync by import
// rather than by copy-pasted string literals.

export const CATEGORIES = [
  { id: "flooding", label: "Flooding" },
  { id: "waterlogging", label: "Waterlogging" },
  { id: "road_damage", label: "Road damage" },
  { id: "construction", label: "Construction hazard" },
  { id: "safety", label: "Safety" },
  { id: "environmental", label: "Environmental" },
  { id: "traffic", label: "Traffic" },
  { id: "other", label: "Other" },
];

export const MAP_LAYERS = [
  {
    id: "raw",
    label: "Raw reports",
    description: "Every report, unverified",
    color: "var(--color-hazard)",
  },
  {
    id: "candidate",
    label: "Candidate clusters",
    description: "Confidence ≥ 25, still gathering reporters",
    color: "var(--color-amber)",
  },
  {
    id: "verified",
    label: "Verified hotspots",
    description: "Confidence ≥ 60, independently confirmed",
    color: "var(--color-verified)",
  },
];

// Consensus-engine thresholds, surfaced in the verification explainer so the
// UI's language matches the backend's actual scoring rules exactly.
export const CONFIDENCE_THRESHOLDS = {
  candidate: 25,
  verified: 60,
  trustRewardOnVerify: 2,
};

export const NAV_LINKS = [
  { href: "#map", label: "Live map" },
  { href: "#how-it-works", label: "How it works" },
  { href: "#report", label: "Report" },
  { href: "#ask", label: "Ask VeriGrid" },
  { href: "#authorities", label: "For authorities" },
  { href: "#faq", label: "FAQ" },
];
