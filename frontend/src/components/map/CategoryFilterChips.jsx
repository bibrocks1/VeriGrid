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
            className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors ${
              isActive
                ? "border-ink-text bg-ink-text/10 text-ink-text"
                : "border-ink-text/25 text-ink-text/50"
            }`}
          >
            {category.label}
          </button>
        );
      })}
    </div>
  );
}
