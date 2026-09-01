"use client";

import { useState } from "react";
import ConfidenceMeter from "./ConfidenceMeter";
import { CONFIDENCE_THRESHOLDS } from "@/lib/constants";

// Interactive demo of the consensus engine: each click simulates one more
// distinct reporter confirming the same hazard, and the confidence score
// climbs in real time, the actual dedup-by-user + threshold logic from the
// build guide, dramatized instead of just described.
const GAIN_PER_REPORTER = 9;

export default function VerificationExplainer() {
  const [reporters, setReporters] = useState(1);

  const confidence = Math.min(reporters * GAIN_PER_REPORTER, 100);
  const status =
    confidence >= CONFIDENCE_THRESHOLDS.verified
      ? "verified"
      : confidence >= CONFIDENCE_THRESHOLDS.candidate
        ? "candidate"
        : "unverified";

  const canAddReporter = confidence < 100;

  return (
    <div className="rounded-3xl bg-card p-6 shadow-soft sm:p-8">
      <p className="text-sm font-medium opacity-60">
        Live simulation, same hazard, independent reporters
      </p>

      <div className="mt-6">
        <ConfidenceMeter
          confidence={confidence}
          status={status === "unverified" ? "candidate" : status}
        />
      </div>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
        <p className="text-sm tabular-nums opacity-80">
          {reporters} distinct reporter{reporters === 1 ? "" : "s"}
          {status === "verified" && (
            <span className="ml-2 font-medium text-verified">
              +{CONFIDENCE_THRESHOLDS.trustRewardOnVerify} trust awarded to each
            </span>
          )}
        </p>
        <button
          type="button"
          onClick={() => setReporters((n) => n + 1)}
          disabled={!canAddReporter}
          className="rounded-full bg-amber px-4 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {canAddReporter ? "Simulate another reporter" : "Fully confirmed"}
        </button>
      </div>
    </div>
  );
}
