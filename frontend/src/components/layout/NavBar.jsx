"use client";

import { useState } from "react";
import { NAV_LINKS } from "@/lib/constants";

export default function NavBar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-4 z-50 flex justify-center px-4">
      <div className="flex w-full max-w-4xl items-center justify-between gap-4 rounded-full bg-card px-3 py-2 shadow-soft">
        <a href="#top" className="flex items-center gap-2 pl-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-ink text-xs font-bold text-ink-text">
            V
          </span>
          <span className="font-display text-base font-bold tracking-tight text-paper-text">
            VeriGrid
          </span>
        </a>

        <nav className="hidden items-center gap-6 lg:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-muted transition-colors hover:text-paper-text"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <a
            href="#report"
            className="hidden items-center rounded-full bg-ink px-5 py-2.5 text-sm font-semibold text-ink-text transition-opacity hover:opacity-90 sm:inline-flex"
          >
            Report an issue
          </a>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-controls="mobile-nav"
            className="flex h-10 w-10 items-center justify-center rounded-full border border-line lg:hidden"
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
          className="absolute top-16 flex w-[calc(100%-2rem)] max-w-4xl flex-col gap-1 rounded-3xl bg-card p-4 shadow-soft lg:hidden"
        >
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              onClick={() => setOpen(false)}
              className="rounded-full px-3 py-2 text-sm font-medium text-paper-text hover:bg-card-soft"
            >
              {link.label}
            </a>
          ))}
        </nav>
      )}
    </header>
  );
}
