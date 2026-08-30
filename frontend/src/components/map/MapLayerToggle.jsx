import { MAP_LAYERS } from "@/lib/constants";

export default function MapLayerToggle({ activeLayers, onToggle }) {
  return (
    <div className="flex flex-wrap gap-2">
      {MAP_LAYERS.map((layer) => {
        const isActive = activeLayers.includes(layer.id);
        return (
          <button
            key={layer.id}
            type="button"
            onClick={() => onToggle(layer.id)}
            aria-pressed={isActive}
            title={layer.description}
            className={`flex items-center gap-2 rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors ${
              isActive
                ? "border-current bg-current/10"
                : "border-line-dark/50 opacity-50"
            }`}
            style={{ color: layer.color }}
          >
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: layer.color }}
              aria-hidden
            />
            {layer.label}
          </button>
        );
      })}
    </div>
  );
}
