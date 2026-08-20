import ConfidenceMeter from "@/components/verification/ConfidenceMeter";

const STATUS_LABEL = {
  draft: "Draft",
  approved: "Approved",
  sent: "Sent",
};

// Structured complaint draft preview (README Hero 7 / Day 11-12): what an
// authority-side reviewer sees before approving a verified cluster for
// dispatch to the identified authority.
export default function AuthorityReportCard({ report }) {
  return (
    <div className="flex flex-col gap-5 rounded-sm border border-line-dark/60 bg-ink-2/60 p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.1em] opacity-60">
            {report.location}
          </p>
          <h3 className="mt-1 font-display text-xl font-bold">
            {report.issueType}
          </h3>
        </div>
        <span className="stamp text-amber">{STATUS_LABEL[report.status]}</span>
      </div>

      <ConfidenceMeter confidence={report.confidence} status="verified" />

      <p className="text-sm leading-relaxed opacity-80">{report.draftText}</p>

      <dl className="grid grid-cols-2 gap-4 border-t border-line-dark/50 pt-4 font-mono text-xs sm:grid-cols-4">
        <div>
          <dt className="opacity-50">Severity</dt>
          <dd className="mt-1">{report.severity}</dd>
        </div>
        <div>
          <dt className="opacity-50">Contributors</dt>
          <dd className="mt-1">{report.contributorCount}</dd>
        </div>
        <div className="col-span-2">
          <dt className="opacity-50">Routed to</dt>
          <dd className="mt-1">{report.identifiedAuthority}</dd>
        </div>
      </dl>
    </div>
  );
}
