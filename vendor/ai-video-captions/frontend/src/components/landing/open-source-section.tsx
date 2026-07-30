"use client";

import { Star, GitFork } from "lucide-react";

import { useIntersectionObserver } from "~/hooks/use-intersection-observer";
import { GithubIcon } from "~/components/icons/github";

export function OpenSourceSection() {
  const { ref, isInView } = useIntersectionObserver({ margin: "-100px" });

  return (
    <section
      ref={ref}
      className="relative bg-white py-20 dark:bg-black"
      style={{ fontFamily: "var(--font-outfit)" }}
    >
      <div className="container mx-auto px-6">
        <div
          className={`reveal mx-auto max-w-3xl text-center ${isInView ? "in-view" : ""}`}
        >
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gray-900 dark:bg-gray-800">
            <GithubIcon className="h-8 w-8 text-white" />
          </div>

          <h2 className="mb-4 text-4xl font-bold text-gray-900 md:text-5xl dark:text-white">
            100% Open Source
          </h2>
          <p className="mb-8 text-lg text-gray-600 dark:text-gray-400">
            No accounts. No data collection. No limits. Self-host with Docker
            Compose in one command. MIT licensed.
          </p>

          <div className="mb-10 flex flex-wrap items-center justify-center gap-4">
            <a
              href="https://github.com/nicolaigaina/ai-video-captions"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-full bg-[#459F94] px-6 py-3 font-semibold text-white transition-colors hover:bg-[#367d74]"
            >
              <Star className="h-4 w-4" />
              Star on GitHub
            </a>
            <a
              href="https://github.com/nicolaigaina/ai-video-captions/fork"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-full border border-gray-300 px-6 py-3 font-semibold text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              <GitFork className="h-4 w-4" />
              Fork
            </a>
          </div>

          {/* Quick start code block */}
          <div
            className={`reveal mx-auto max-w-md overflow-hidden rounded-2xl bg-gray-900 text-left shadow-lg dark:bg-gray-800 ${isInView ? "in-view" : ""}`}
            style={{ "--stagger": "0.2s" } as React.CSSProperties}
          >
            <div className="flex items-center gap-2 border-b border-gray-700 px-4 py-3">
              <div className="h-3 w-3 rounded-full bg-red-500" />
              <div className="h-3 w-3 rounded-full bg-yellow-500" />
              <div className="h-3 w-3 rounded-full bg-green-500" />
              <span className="ml-2 text-xs text-gray-400">terminal</span>
            </div>
            <div className="p-4 font-mono text-sm text-gray-300">
              <p>
                <span className="text-green-400">$</span> git clone
                https://github.com/nicolaigaina/
              </p>
              <p className="pl-4">ai-video-captions.git</p>
              <p className="mt-1">
                <span className="text-green-400">$</span> cd ai-video-captions
              </p>
              <p className="mt-1">
                <span className="text-green-400">$</span> docker compose up
              </p>
              <p className="mt-2 text-gray-500">
                # Open http://localhost:3000
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
