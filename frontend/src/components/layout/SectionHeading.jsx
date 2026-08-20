// Eyebrow + headline + optional description, shared by every section so the
// typographic rhythm (label → display headline → body copy) stays identical
// across the whole scroll. The eyebrow reads like a map-legend entry: a
// small colored swatch and a mono caps label, not a decorative kicker.

export default function SectionHeading({
  eyebrow,
  eyebrowColor = "var(--color-amber)",
  title,
  description,
  align = "left",
  children,
}) {
  return (
    <div
      className={
        align === "center" ? "mx-auto max-w-2xl text-center" : "max-w-2xl"
      }
    >
      {eyebrow && (
        <div
          className={`mb-4 flex items-center gap-2 font-mono text-xs uppercase tracking-[0.18em] opacity-80 ${
            align === "center" ? "justify-center" : ""
          }`}
        >
          <span
            className="h-2 w-2 rounded-full"
            style={{ backgroundColor: eyebrowColor }}
            aria-hidden
          />
          {eyebrow}
        </div>
      )}
      <h2 className="font-display text-3xl font-bold leading-tight tracking-tight sm:text-4xl">
        {title}
      </h2>
      {description && (
        <p className="mt-4 text-base leading-relaxed opacity-80 sm:text-lg">
          {description}
        </p>
      )}
      {children}
    </div>
  );
}
