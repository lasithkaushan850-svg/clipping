"use client";

import Link from "next/link";
import { Mail, ExternalLink } from "lucide-react";
import { GithubIcon } from "~/components/icons/github";

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer
      className="relative bg-gray-900 text-white"
      style={{ fontFamily: "var(--font-outfit)" }}
    >
      <div className="relative z-10 container mx-auto px-6 py-16">
        <div className="grid grid-cols-1 gap-12 md:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div className="md:col-span-2 lg:col-span-1">
            <Link href="/" className="mb-4 inline-block">
              <span className="text-2xl font-bold tracking-tight">
                <span className="bg-gradient-to-r from-[#459F94] to-[#367d74] bg-clip-text text-transparent">
                  AI
                </span>
                <span className="text-white"> Captions</span>
              </span>
            </Link>
            <p className="mb-6 max-w-xs text-gray-400">
              Free, open-source AI video caption generator. Self-hosted,
              private, no limits.
            </p>
            <div className="flex gap-3">
              <a
                href="https://github.com/nicolaigaina/ai-video-captions"
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-full bg-gray-800 p-3 transition-colors hover:bg-[#459F94]"
                aria-label="GitHub"
              >
                <GithubIcon className="h-5 w-5" />
              </a>
              <a
                href="mailto:admin@autoshorts.app"
                className="rounded-full bg-gray-800 p-3 transition-colors hover:bg-[#459F94]"
                aria-label="Email"
              >
                <Mail className="h-5 w-5" />
              </a>
            </div>
          </div>

          {/* Product */}
          <div>
            <h3 className="mb-4 text-lg font-semibold">Product</h3>
            <ul className="space-y-3">
              <li>
                <Link
                  href="/"
                  className="text-gray-400 transition-colors hover:text-white"
                >
                  Generate Captions
                </Link>
              </li>
              <li>
                <Link
                  href="/history"
                  className="text-gray-400 transition-colors hover:text-white"
                >
                  Caption History
                </Link>
              </li>
              <li>
                <a
                  href="https://github.com/nicolaigaina/ai-video-captions#quick-start"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-400 transition-colors hover:text-white"
                >
                  Self-Host Guide
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/nicolaigaina/ai-video-captions/blob/main/docs/API.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-400 transition-colors hover:text-white"
                >
                  API Docs
                </a>
              </li>
            </ul>
          </div>

          {/* Open Source */}
          <div>
            <h3 className="mb-4 text-lg font-semibold">Open Source</h3>
            <ul className="space-y-3">
              <li>
                <a
                  href="https://github.com/nicolaigaina/ai-video-captions"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-400 transition-colors hover:text-white"
                >
                  GitHub Repository
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/nicolaigaina/ai-video-captions/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-400 transition-colors hover:text-white"
                >
                  Report a Bug
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/nicolaigaina/ai-video-captions/blob/main/CONTRIBUTING.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-400 transition-colors hover:text-white"
                >
                  Contributing Guide
                </a>
              </li>
              <li>
                <span className="rounded-full border border-gray-700 px-2 py-0.5 text-xs text-gray-400">
                  MIT License
                </span>
              </li>
            </ul>
          </div>

          {/* Built By */}
          <div>
            <h3 className="mb-4 text-lg font-semibold">Built By</h3>
            <ul className="space-y-3">
              <li>
                <a
                  href="https://autoshorts.app"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-gray-400 transition-colors hover:text-white"
                >
                  AutoShorts
                  <ExternalLink className="h-3 w-3" />
                </a>
              </li>
              <li>
                <span className="text-sm text-gray-500">
                  AI-powered video repurposing for content creators
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-12 border-t border-gray-800 pt-8">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <p className="text-sm text-gray-400">
              &copy; {currentYear} AI Video Captions. All rights reserved.
            </p>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>
                Made by the team behind{" "}
                <a
                  href="https://autoshorts.app"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[#459F94] hover:underline"
                >
                  AutoShorts
                </a>
              </span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
