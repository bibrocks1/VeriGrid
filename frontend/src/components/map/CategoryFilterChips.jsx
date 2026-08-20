import { CATEGORIES } from "@/lib/constants";

export default function CategoryFilterChips({ activeCategories, onToggle }) {
  return (
    <div className="flex flex-wrap gap-2">
      {CATEGORIES.map((category) => {
        const isActive = activeCategories.includes(category.id);
        return (
          <button
            key={category.id}
            type="button"
            onClick={() => onToggle(category.id)}
            aria-pressed={isActive}
            className={`rounded-full border px-3 py-1 font-mono text-[0.65rem] uppercase tracking-[0.08em] transition-colors ${
              isActive
                ? "border-ink-text bg-ink-text/10 text-ink-text"
                : "border-ink-text/30 text-ink-text/50"
            }`}
          >
            {category.label}
          </button>
        );
      })}
    </div>
  );
}
