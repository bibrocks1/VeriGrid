"use client";

import { useState } from "react";
import AuthorityReportCard from "./AuthorityReportCard";
import { sendAuthorityReport } from "@/lib/api";

// Approve & Send flow: draft -> approved -> sent, matching the status states
// called out in the build guide. Approval is a separate, explicit step from
// sending so a reviewer can sign off before anything reaches the authority.
export default function ReportReviewScreen({ initialReport }) {
  const [report, setReport] = useState(initialReport);
  const [sending, setSending] = useState(false);

  function approve() {
    setReport((current) => ({ ...current, status: "approved" }));
  }

  async function send() {
    setSending(true);
    const { data } = await sendAuthorityReport(report.clusterId);
    setReport(data);
    setSending(false);
  }

  return (
    <div className="flex flex-col gap-6">
      <AuthorityReportCard report={report} />

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={approve}
          disabled={report.status !== "draft"}
          className="rounded-sm bg-amber px-4 py-2 font-mono text-xs uppercase tracking-[0.1em] text-ink disabled:cursor-not-allowed disabled:opacity-40"
        >
          Approve
        </button>
        <button
          type="button"
          onClick={send}
          disabled={report.status !== "approved" || sending}
          className="rounded-sm bg-verified px-4 py-2 font-mono text-xs uppercase tracking-[0.1em] text-ink-text disabled:cursor-not-allowed disabled:opacity-40"
        >
          {sending ? "Sending…" : "Approve & send"}
        </button>
      </div>
    </div>
  );
}
