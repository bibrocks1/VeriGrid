"use client";

import { useState } from "react";
import { NAV_LINKS } from "@/lib/constants";

export default function NavBar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-line bg-paper/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <a href="#top" className="flex items-baseline gap-2">
          <span className="font-display text-xl font-bold tracking-tight text-paper-text">
            VeriGrid
          </span>
          <span className="hidden font-mono text-[0.65rem] uppercase tracking-[0.16em] text-muted-ink sm:inline">
            powered by MirEye
          </span>
        </a>

        <nav className="hidden items-center gap-7 lg:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="font-mono text-xs uppercase tracking-[0.1em] text-paper-text/70 transition-colors hover:text-paper-text"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <a
            href="#map"
            className="hidden rounded-sm bg-ink px-4 py-2 font-mono text-xs uppercase tracking-[0.1em] text-ink-text transition-colors hover:bg-ink-2 sm:inline-block"
          >
            Open live map
          </a>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-controls="mobile-nav"
            className="flex h-9 w-9 items-center justify-center rounded-sm border border-line lg:hidden"
          >
            <span className="sr-only">Toggle navigation</span>
            <div className="flex flex-col gap-1">
              <span className="h-px w-4 bg-paper-text" />
              <span className="h-px w-4 bg-paper-text" />
              <span className="h-px w-4 bg-paper-text" />
            </div>
          </button>
        </div>
      </div>

      {open && (
        <nav
          id="mobile-nav"
          className="flex flex-col gap-1 border-t border-line px-6 py-3 lg:hidden"
        >
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              onClick={() => setOpen(false)}
              className="py-2 font-mono text-xs uppercase tracking-[0.1em] text-paper-text/80"
            >
              {link.label}
            </a>
          ))}
        </nav>
      )}
    </header>
  );
}
