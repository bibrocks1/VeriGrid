// Generic full-bleed section wrapper reused by every hero (README §2:
// "HeroSection (generic wrapper)"). `tone` picks ink vs paper coloring and
// the matching watermark texture; everything else is content passed as
// children so each section controls its own layout.

const TONE_STYLES = {
  ink: "bg-ink text-ink-text bg-contour",
  paper: "bg-paper text-paper-text bg-grid-paper",
  paper2: "bg-paper-2 text-paper-text",
};

export default function Section({
  id,
  tone = "paper",
  className = "",
  children,
}) {
  return (
    <section
      id={id}
      className={`border-b border-line/60 ${tone === "ink" ? "border-line-dark/60" : ""} ${TONE_STYLES[tone]} ${className}`}
    >
      <div className="mx-auto max-w-7xl px-6 py-20 sm:py-28">{children}</div>
    </section>
  );
}
