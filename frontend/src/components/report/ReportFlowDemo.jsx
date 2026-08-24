"use client";

import { useState } from "react";
import ReportForm from "./ReportForm";
import ReportConfirmation from "./ReportConfirmation";
import NearbyReportsList from "@/components/map/NearbyReportsList";
import { MOCK_CENTER } from "@/lib/mockData";

// Standalone report-flow demo for Hero 3, same ReportForm/ReportConfirmation
// building blocks the live map uses for click-to-report, but with a fixed
// default location so it works as a self-contained walkthrough.
export default function ReportFlowDemo() {
  const [submitted, setSubmitted] = useState(null);

  return (
    <div className="rounded-3xl bg-card p-6 shadow-soft sm:p-8">
      {submitted ? (
        <ReportConfirmation report={submitted} onReset={() => setSubmitted(null)} />
      ) : (
        <>
          <NearbyReportsList lat={MOCK_CENTER.lat} lng={MOCK_CENTER.lng} />
          <ReportForm location={MOCK_CENTER} onSubmitted={setSubmitted} />
        </>
      )}
    </div>
  );
}
