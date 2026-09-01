import { NAV_LINKS } from "@/lib/constants";

export default function Footer() {
  const isDemoMode = !process.env.NEXT_PUBLIC_API_URL;

  return (
    <footer className="border-t border-line bg-card">
      <div className="mx-auto max-w-6xl px-6 py-14">
        <div className="flex flex-col gap-10 sm:flex-row sm:justify-between">
          <div className="max-w-xs">
            <span className="font-display text-lg font-bold text-paper-text">
              VeriGrid
            </span>
            <p className="mt-3 text-sm leading-relaxed text-muted">
              Crowdsourced hazard verification, backed by MirEye infrastructure
              data. Built to route confirmed issues to the right authority,
              fast.
            </p>
          </div>

          <nav className="flex flex-wrap gap-x-8 gap-y-3">
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="text-sm font-medium text-muted transition-colors hover:text-paper-text"
              >
                {link.label}
              </a>
            ))}
            <a
              href="https://github.com"
              className="text-sm font-medium text-muted transition-colors hover:text-paper-text"
            >
              GitHub
            </a>
          </nav>
        </div>

        <div className="mt-12 flex flex-col gap-3 border-t border-line pt-6 text-sm text-muted sm:flex-row sm:items-center sm:justify-between">
          <p>
            © {new Date().getFullYear()} VeriGrid. Built for a 14-day pilot.
          </p>
          {isDemoMode && (
            <p className="badge bg-amber/15 text-amber">Demo mode, mock data</p>
          )}
        </div>
      </div>
    </footer>
  );
}
