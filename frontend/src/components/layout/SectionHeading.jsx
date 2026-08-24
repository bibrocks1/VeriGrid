// Section header: headline + optional description. No eyebrow label by
// default — the reference reserves that small icon+text treatment for the
// hero alone, and repeating a small-caps label above every section reads
// as templated. Pass `eyebrow` only for the rare section that genuinely
// needs one.
export default function SectionHeading({
  eyebrow,
  title,
  description,
  align = "left",
  children,
}) {
  return (
    <div className={align === "center" ? "mx-auto max-w-2xl text-center" : "max-w-2xl"}>
      {eyebrow && (
        <p
          className={`mb-3 flex items-center gap-2 text-sm font-medium text-muted ${
            align === "center" ? "justify-center" : ""
          }`}
        >
          {eyebrow}
        </p>
      )}
      <h2 className="font-display text-3xl font-extrabold tracking-tight leading-[1.1] sm:text-4xl">
        {title}
      </h2>
      {description && (
        <p className="mt-4 text-base leading-relaxed text-muted sm:text-lg">{description}</p>
      )}
      {children}
    </div>
  );
}
