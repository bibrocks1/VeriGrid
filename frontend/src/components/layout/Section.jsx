// Generic full-bleed section wrapper reused by every part of the page.
// The page has one theme (light paper canvas) with exactly one deliberate
// dark section — the live map — rather than alternating dark/light per
// section. Everything else sits on the same warm-neutral paper background,
// with individual cards providing local contrast instead of section-level
// theme swaps.
const TONE_STYLES = {
  paper: "bg-paper text-paper-text",
  ink: "bg-ink text-ink-text",
};

export default function Section({
  id,
  tone = "paper",
  className = "",
  children,
}) {
  return (
    <section id={id} className={`${TONE_STYLES[tone]} ${className}`}>
      <div className="mx-auto max-w-6xl px-6 py-20 sm:py-28">{children}</div>
    </section>
  );
}
