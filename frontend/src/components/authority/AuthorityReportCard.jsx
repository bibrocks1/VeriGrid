import ConfidenceMeter from "@/components/verification/ConfidenceMeter";

const STATUS_LABEL = {
  draft: "Draft",
  approved: "Approved",
  sent: "Sent",
};

// Structured complaint draft preview: what an authority-side reviewer sees
// before approving a verified cluster for dispatch to the identified
// authority.
export default function AuthorityReportCard({ report }) {
  return (
    <div className="flex flex-col gap-5 rounded-3xl bg-card p-6 shadow-soft sm:p-8">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium opacity-60">{report.location}</p>
          <h3 className="mt-1 font-display text-xl font-bold">
            {report.issueType}
          </h3>
        </div>
        <span className="badge bg-amber/15 text-amber">
          {STATUS_LABEL[report.status]}
        </span>
      </div>

      <ConfidenceMeter confidence={report.confidence} status="verified" />

      <p className="text-sm leading-relaxed opacity-80">{report.draftText}</p>

      <dl className="grid grid-cols-2 gap-4 border-t border-line pt-4 text-sm sm:grid-cols-4">
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
