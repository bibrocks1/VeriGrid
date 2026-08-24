// Generic numbered-step flow graphic, reused for the report pipeline and
// the verification explainer. Numbering is justified here specifically
// because both are real ordered pipelines, not just lists.

export default function StepDiagram({ steps }) {
  return (
    <ol className="grid grid-cols-1 gap-6 sm:grid-cols-4 sm:gap-4">
      {steps.map((step, i) => (
        <li key={step.title} className="flex flex-col gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-card text-sm font-semibold shadow-soft">
            {i + 1}
          </span>
          <h3 className="font-display text-lg font-semibold">{step.title}</h3>
          <p className="text-sm leading-relaxed opacity-70">{step.description}</p>
        </li>
      ))}
    </ol>
  );
}
