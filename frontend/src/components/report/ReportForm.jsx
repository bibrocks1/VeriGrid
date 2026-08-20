"use client";

import { useState } from "react";
import { CATEGORIES } from "@/lib/constants";
import { createReport } from "@/lib/api";

// Reusable report submission form. `location` is controlled by the caller
// (set from a map click, or left null for the standalone demo in Hero 3) so
// this component only owns its own field state and the submit request.
export default function ReportForm({ location, onSubmitted, onCancel }) {
  const [category, setCategory] = useState(CATEGORIES[0].id);
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!description.trim()) {
      setError("Add a short description so verifiers know what to look for.");
      return;
    }
    setError(null);
    setSubmitting(true);
    const { data } = await createReport({
      category,
      description: description.trim(),
      lat: location?.lat,
      lng: location?.lng,
    });
    setSubmitting(false);
    onSubmitted(data);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div>
        <label className="font-mono text-xs uppercase tracking-[0.1em] opacity-70">
          Category
        </label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="mt-1.5 w-full rounded-sm border border-line bg-transparent px-3 py-2 text-sm"
        >
          {CATEGORIES.map((c) => (
            <option key={c.id} value={c.id}>
              {c.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="font-mono text-xs uppercase tracking-[0.1em] opacity-70">
          Description
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          placeholder="What's happening, and how bad is it right now?"
          className="mt-1.5 w-full rounded-sm border border-line bg-transparent px-3 py-2 text-sm"
        />
      </div>

      <div className="font-mono text-xs uppercase tracking-[0.1em] opacity-60">
        Location:{" "}
        {location
          ? `${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}`
          : "Click the map to drop a pin, or submit at the default center"}
      </div>

      {error && <p className="text-xs text-hazard">{error}</p>}

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={submitting}
          className="flex-1 rounded-sm bg-hazard px-4 py-2 font-mono text-xs uppercase tracking-[0.1em] text-ink-text transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {submitting ? "Submitting…" : "Submit report"}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-sm border border-line px-4 py-2 font-mono text-xs uppercase tracking-[0.1em] opacity-70"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
