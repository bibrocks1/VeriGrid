"use client";

import { useState } from "react";
import ReportForm from "./ReportForm";
import ReportConfirmation from "./ReportConfirmation";
import { MOCK_CENTER } from "@/lib/mockData";

// Standalone report-flow demo for Hero 3 — same ReportForm/ReportConfirmation
// building blocks the live map uses for click-to-report, but with a fixed
// default location so it works as a self-contained walkthrough.
export default function ReportFlowDemo() {
  const [submitted, setSubmitted] = useState(null);

  return (
    <div className="rounded-sm border border-line bg-paper-2/50 p-6 sm:p-8">
      {submitted ? (
        <ReportConfirmation
          report={submitted}
          onReset={() => setSubmitted(null)}
        />
      ) : (
        <ReportForm location={MOCK_CENTER} onSubmitted={setSubmitted} />
      )}
    </div>
  );
}
