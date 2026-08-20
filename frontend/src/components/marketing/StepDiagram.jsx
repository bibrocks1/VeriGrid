// Generic numbered-step flow graphic, reused for the report pipeline
// (Hero 3) and the verification explainer (Hero 4). Numbering is justified
// here specifically because both are real ordered pipelines, not just lists.

export default function StepDiagram({ steps }) {
  return (
    <ol className="grid grid-cols-1 gap-0 sm:grid-cols-4">
      {steps.map((step, i) => (
        <li
          key={step.title}
          className="relative flex flex-col gap-3 px-0 py-6 sm:px-6"
        >
          {i < steps.length - 1 && (
            <span
              className="absolute right-0 top-9 hidden h-px w-6 translate-x-full bg-current opacity-30 sm:block"
              aria-hidden
            />
          )}
          <span className="font-mono text-xs tabular-nums opacity-50">
            {String(i + 1).padStart(2, "0")}
          </span>
          <h3 className="font-display text-lg font-semibold">{step.title}</h3>
          <p className="text-sm leading-relaxed opacity-70">
            {step.description}
          </p>
        </li>
      ))}
    </ol>
  );
}
