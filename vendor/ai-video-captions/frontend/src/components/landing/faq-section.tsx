"use client";

import { ChevronDown } from "lucide-react";
import { useState } from "react";
import { useIntersectionObserver } from "~/hooks/use-intersection-observer";

const faqs = [
  {
    question: "What video formats are supported?",
    answer:
      "We support MP4, MOV, and WebM video files. Most videos from phones, cameras, and screen recorders work out of the box.",
  },
  {
    question: "How long does processing take?",
    answer:
      "It depends on video length and your hardware. Roughly 1-3 minutes per minute of video on a modern CPU. Shorter videos process in seconds.",
  },
  {
    question: "What languages are supported?",
    answer:
      "Over 100 languages are supported via automatic detection. The AI transcription identifies the spoken language and selects appropriate fonts for each script.",
  },
  {
    question: "Can I customize caption position?",
    answer:
      "Yes! Use our interactive phone mockup to drag captions anywhere from 5% to 50% from the bottom. Preset buttons for Top, Middle, and Bottom positions.",
  },
  {
    question: "What's the max file size?",
    answer:
      "Default limits are 500MB and 30 minutes, but these are configurable via environment variables when self-hosting. Adjust them to match your server's capabilities.",
  },
  {
    question: "How is this different from other caption tools?",
    answer:
      "It's fully self-hosted and open-source. Your videos stay on your infrastructure. No accounts, no uploads to third parties, no usage limits, and no vendor lock-in.",
  },
];

export function FAQSection() {
  const { ref, isInView } = useIntersectionObserver({ margin: "-100px" });
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section
      id="faq"
      ref={ref}
      className="relative bg-gray-50 py-20 dark:bg-gray-900"
      style={{ fontFamily: "var(--font-outfit)" }}
    >
      <div className="relative z-10 container mx-auto px-6">
        {/* Header */}
        <div
          className={`reveal mb-12 text-center ${isInView ? "in-view" : ""}`}
        >
          <h2 className="mb-4 text-4xl font-bold text-gray-900 md:text-5xl dark:text-white">
            Frequently Asked{" "}
            <span className="bg-gradient-to-r from-[#459F94] to-[#EDB118] bg-clip-text text-transparent">
              Questions
            </span>
          </h2>
          <p className="mx-auto max-w-2xl text-lg text-gray-600 dark:text-gray-400">
            Everything you need to know about AI Video Captions.
          </p>
        </div>

        {/* FAQ Grid */}
        <div className="mx-auto grid max-w-4xl grid-cols-1 gap-4 md:grid-cols-2 md:gap-6">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className={`reveal rounded-2xl bg-white p-6 shadow-sm transition-all dark:bg-gray-800 ${
                index >= 4 ? "md:col-span-2" : ""
              } ${isInView ? "in-view" : ""}`}
              style={
                { "--stagger": `${index * 0.1}s` } as React.CSSProperties
              }
            >
              <button
                onClick={() =>
                  setOpenIndex(openIndex === index ? null : index)
                }
                aria-expanded={openIndex === index}
                className="flex w-full cursor-pointer items-start justify-between gap-4 text-left"
              >
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {faq.question}
                </h3>
                <ChevronDown
                  className={`h-5 w-5 flex-shrink-0 text-[#459F94] transition-transform ${
                    openIndex === index ? "rotate-180" : ""
                  }`}
                />
              </button>
              <div
                className={`overflow-hidden transition-all duration-300 ${
                  openIndex === index
                    ? "mt-4 max-h-96 opacity-100"
                    : "max-h-0 opacity-0"
                }`}
              >
                <p className="text-gray-600 dark:text-gray-400">{faq.answer}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
