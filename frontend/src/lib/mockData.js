// Demo-mode fixtures. Shaped exactly like the payloads the real endpoints
// documented in lib/api.js are expected to return, so swapping a live
// backend in later is a data-shape-compatible change, not a rewrite.
// Locations are a fictional ward — no real hazard or address claims.

export const MOCK_CENTER = { lat: 12.9716, lng: 77.5946 };

export const MOCK_REPORTS = [
  {
    id: "r-101",
    category: "waterlogging",
    description:
      "Ankle-deep water outside the Ward 4 market gate since morning rain.",
    lat: 12.9741,
    lng: 77.5958,
    createdAt: "2026-08-19T06:40:00Z",
    reporterTrust: 61,
  },
  {
    id: "r-102",
    category: "road_damage",
    description:
      "Pothole cluster after the flyover ramp, cars swerving into the bike lane.",
    lat: 12.9689,
    lng: 77.5901,
    createdAt: "2026-08-19T09:12:00Z",
    reporterTrust: 44,
  },
  {
    id: "r-103",
    category: "construction",
    description: "Unbarricaded trench along the footpath near Cross Street 9.",
    lat: 12.9702,
    lng: 77.6003,
    createdAt: "2026-08-20T05:02:00Z",
    reporterTrust: 38,
  },
];

export const MOCK_CLUSTERS = [
  {
    id: "c-201",
    category: "waterlogging",
    status: "verified",
    confidence: 78,
    description:
      "Recurring waterlogging at the Ward 4 market underpass during heavy rain.",
    lat: 12.9744,
    lng: 77.5961,
    reporterCount: 9,
    distinctReporters: 9,
    firstReportedAt: "2026-08-17T05:10:00Z",
    verifiedAt: "2026-08-18T14:22:00Z",
  },
  {
    id: "c-202",
    category: "road_damage",
    status: "candidate",
    confidence: 41,
    description: "Growing pothole belt on the flyover exit ramp.",
    lat: 12.9686,
    lng: 77.5897,
    reporterCount: 4,
    distinctReporters: 4,
    firstReportedAt: "2026-08-19T08:40:00Z",
    verifiedAt: null,
  },
  {
    id: "c-203",
    category: "safety",
    status: "candidate",
    confidence: 29,
    description:
      "Streetlight outage along the canal walkway, reported unsafe after dusk.",
    lat: 12.976,
    lng: 77.5889,
    reporterCount: 3,
    distinctReporters: 3,
    firstReportedAt: "2026-08-19T18:05:00Z",
    verifiedAt: null,
  },
  {
    id: "c-204",
    category: "environmental",
    status: "verified",
    confidence: 66,
    description:
      "Open garbage burning near the canal bank, smoke reaching residential blocks.",
    lat: 12.9668,
    lng: 77.5972,
    reporterCount: 7,
    distinctReporters: 6,
    firstReportedAt: "2026-08-15T07:00:00Z",
    verifiedAt: "2026-08-16T10:11:00Z",
  },
];

export const MOCK_STATS = {
  activeReports: 132,
  verifiedHotspots: 28,
  trustContributors: 411,
};

export const MOCK_CHAT_HISTORY = [
  {
    id: "m-1",
    role: "assistant",
    source: null,
    text: "Ask me about hazards or infrastructure near a point on the map — I'll pull from verified VeriGrid reports and MirEye's infrastructure records.",
  },
];

export const MOCK_AUTHORITY_REPORT = {
  clusterId: "c-201",
  issueType: "Waterlogging",
  location: "Ward 4 Market Underpass, Cross Street 9",
  severity: "High",
  confidence: 78,
  contributorCount: 9,
  identifiedAuthority: "Ward 4 Municipal Engineering Office",
  status: "draft",
  draftText:
    "Recurring waterlogging reported at the Ward 4 market underpass during rainfall, confirmed by 9 independent reporters over 36 hours. Confidence score 78/100 (verified). Requests drainage inspection ahead of the next forecast rainfall.",
};

export const MOCK_SYNC_LOG = {
  lastSyncedAt: "2026-08-20T04:15:00Z",
  status: "ok",
  recordsSynced: 214,
};
