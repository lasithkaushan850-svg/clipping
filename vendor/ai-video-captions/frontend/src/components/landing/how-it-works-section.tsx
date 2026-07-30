"use client";

import { Fragment } from "react";
import { Upload, Palette, Download, Mic, Flame } from "lucide-react";
import { useIntersectionObserver } from "~/hooks/use-intersection-observer";

const steps = [
  {
    number: "1",
    title: "Upload Video",
    description:
      "Drop any MP4, MOV, or WebM video. Up to 500MB and 30 minutes.",
    icon: Upload,
    pills: ["MP4, MOV, WebM", "Up to 500MB", "Up to 30 min"],
  },
  {
    number: "2",
    title: "Pick a Style",
    description:
      "Choose from 6 trending caption styles. Preview the look in real-time with our interactive phone mockup.",
    icon: Palette,
    pills: ["6 styles", "Live preview", "Drag to position"],
  },
  {
    number: "3",
    title: "Download",
    description:
      "Your captioned video is ready. Download in full HD quality.",
    icon: Download,
    pills: ["HD quality", "CRF 18", "Audio preserved"],
  },
];

const pipelineSteps = [
  { icon: Upload, label: "Upload" },
  { icon: Mic, label: "Transcribe" },
  { icon: Palette, label: "Style" },
  { icon: Flame, label: "Burn" },
  { icon: Download, label: "Export" },
];

export function HowItWorksSection() {
  const { ref, isInView } = useIntersectionObserver({ margin: "-80px" });

  return (
    <section
      id="how-it-works"
      ref={ref}
      className="relative bg-white py-24 dark:bg-black"
      style={{ fontFamily: "var(--font-outfit)" }}
    >
      <div className="container mx-auto px-6">
        {/* Section heading */}
        <div className={`reveal mb-16 ${isInView ? "in-view" : ""}`}>
          <h2 className="mb-4 text-center text-4xl font-bold text-gray-900 md:text-5xl dark:text-white">
            How It{" "}
            <span className="bg-gradient-to-r from-[#459F94] to-[#EDB118] bg-clip-text text-transparent">
              Works
            </span>
          </h2>
          <p className="mx-auto max-w-2xl text-center text-lg text-gray-600 dark:text-gray-400">
            Three simple steps from raw video to captioned masterpiece.
          </p>
        </div>

        {/* Pipeline visualization */}
        <div
          className={`reveal mx-auto mb-20 max-w-3xl rounded-2xl bg-gray-900 p-6 shadow-lg sm:p-8 dark:bg-gray-800 ${isInView ? "in-view" : ""}`}
          style={{ "--stagger": "0.2s" } as React.CSSProperties}
        >
          <div className="flex items-center justify-between gap-1 sm:gap-2">
            {pipelineSteps.map((step, i) => (
              <Fragment key={step.label}>
                <div
                  className={`reveal-scale flex flex-col items-center gap-2 ${isInView ? "in-view" : ""}`}
                  style={
                    {
                      "--stagger": `${0.3 + i * 0.15}s`,
                    } as React.CSSProperties
                  }
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-r from-[#459F94] to-[#EDB118] shadow-lg shadow-[#459F94]/20 sm:h-12 sm:w-12">
                    <step.icon className="h-4 w-4 text-white sm:h-5 sm:w-5" />
                  </div>
                  <span className="hidden text-xs font-medium text-gray-400 sm:block">
                    {step.label}
                  </span>
                </div>

                {i < pipelineSteps.length - 1 && (
                  <div
                    className={`h-0.5 flex-1 origin-left bg-gradient-to-r from-[#459F94] to-[#EDB118] transition-transform duration-300 ${isInView ? "scale-x-100" : "scale-x-0"}`}
                    style={{ transitionDelay: `${0.4 + i * 0.15}s` }}
                  />
                )}
              </Fragment>
            ))}
          </div>
        </div>

        {/* Steps */}
        <div className="mx-auto max-w-4xl space-y-16">
          {steps.map((step, index) => {
            const isEven = index % 2 === 0;
            return (
              <div
                key={step.number}
                className={`reveal flex flex-col items-center gap-8 lg:gap-12 ${
                  isEven ? "lg:flex-row" : "lg:flex-row-reverse"
                } ${isInView ? "in-view" : ""}`}
                style={
                  {
                    "--stagger": `${0.2 + index * 0.15}s`,
                  } as React.CSSProperties
                }
              >
                {/* Number circle */}
                <div className="flex shrink-0 items-center justify-center">
                  <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-r from-[#459F94] to-[#EDB118] text-3xl font-bold text-white shadow-lg shadow-[#459F94]/20">
                    {step.number}
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 text-center lg:text-left">
                  <div className="mb-3 inline-flex items-center gap-2">
                    <step.icon className="h-5 w-5 text-[#459F94]" />
                    <h3 className="text-2xl font-bold text-gray-900 sm:text-3xl dark:text-white">
                      {step.title}
                    </h3>
                  </div>
                  <p className="text-base leading-relaxed text-gray-600 sm:text-lg dark:text-gray-400">
                    {step.description}
                  </p>

                  {/* Feature pills */}
                  <div className="mt-4 flex flex-wrap justify-center gap-2 lg:justify-start">
                    {step.pills.map((pill) => (
                      <span
                        key={pill}
                        className="rounded-full bg-[#459F94]/10 px-3 py-1 text-xs font-medium text-[#459F94] dark:bg-[#459F94]/20"
                      >
                        {pill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
