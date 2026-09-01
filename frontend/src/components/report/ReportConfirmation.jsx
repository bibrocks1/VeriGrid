export default function ReportConfirmation({ report, onReset }) {
  return (
    <div className="flex flex-col gap-4">
      <span className="badge w-fit bg-verified/15 text-verified">
        Report received
      </span>
      <p className="text-sm leading-relaxed opacity-80">
        Your report is now live on the map as an unverified point. Once 2+
        independent reporters confirm the same hazard nearby, it becomes a
        candidate cluster, and at 60+ confidence, a verified hotspot.
      </p>
      <dl className="grid grid-cols-2 gap-3 border-t border-current/15 pt-4 text-sm">
        <div>
          <dt className="opacity-50">Category</dt>
          <dd className="mt-1 capitalize">{report.category}</dd>
        </div>
        <div>
          <dt className="opacity-50">Report ID</dt>
          <dd className="mt-1">{report.id}</dd>
        </div>
      </dl>
      {onReset && (
        <button
          type="button"
          onClick={onReset}
          className="w-fit text-sm font-semibold text-hazard"
        >
          Submit another report
        </button>
      )}
    </div>
  );
}
