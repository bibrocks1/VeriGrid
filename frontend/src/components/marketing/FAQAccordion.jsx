"use client";

import { useState } from "react";

export default function FAQAccordion({ items }) {
  const [openIndex, setOpenIndex] = useState(0);

  return (
    <div className="divide-y divide-line">
      {items.map((item, i) => {
        const isOpen = openIndex === i;
        return (
          <div key={item.question} className="px-4">
            <button
              type="button"
              onClick={() => setOpenIndex(isOpen ? -1 : i)}
              aria-expanded={isOpen}
              className="flex w-full items-center justify-between gap-4 py-5 text-left"
            >
              <span className="font-display text-base font-semibold sm:text-lg">
                {item.question}
              </span>
              <span
                className="text-xl leading-none opacity-60 transition-transform"
                style={{ transform: isOpen ? "rotate(45deg)" : "none" }}
                aria-hidden
              >
                +
              </span>
            </button>
            {isOpen && (
              <p className="pb-5 pr-10 text-sm leading-relaxed opacity-75">
                {item.answer}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
