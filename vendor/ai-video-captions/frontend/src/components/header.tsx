"use client";

import Link from "next/link";
import { useTheme } from "next-themes";
import { useEffect, useState, useSyncExternalStore } from "react";
import { History, Menu, Moon, Sun, X } from "lucide-react";
import { GithubIcon } from "~/components/icons/github";

const subscribe = () => () => {};
function useHasMounted() {
  return useSyncExternalStore(subscribe, () => true, () => false);
}

export function Header() {
  const { theme, setTheme } = useTheme();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const mounted = useHasMounted();

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 50);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 right-0 left-0 z-50 transition-all duration-300 ${
        isScrolled
          ? "border-b border-gray-200/50 bg-white/80 shadow-md backdrop-blur-lg dark:border-gray-800/50 dark:bg-black/80"
          : "bg-white dark:bg-black"
      }`}
      style={{ fontFamily: "var(--font-outfit)" }}
    >
      <nav className="container mx-auto flex items-center justify-between px-6 py-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <span className="text-xl font-bold tracking-tight sm:text-2xl">
            <span className="bg-gradient-to-r from-[#459F94] to-[#367d74] bg-clip-text text-transparent">
              AI
            </span>
            <span className="text-gray-900 dark:text-white">/</span>
            <span className="bg-gradient-to-r from-[#EDB118] to-[#d9a515] bg-clip-text text-transparent">
              Captions
            </span>
          </span>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden items-center gap-6 md:flex">
          <Link
            href="/"
            className="text-gray-700 transition-colors hover:text-[#459F94] dark:text-gray-300 dark:hover:text-[#459F94]"
          >
            Home
          </Link>
          <Link
            href="/history"
            className="text-gray-700 transition-colors hover:text-[#459F94] dark:text-gray-300 dark:hover:text-[#459F94]"
          >
            History
          </Link>
          <a
            href="https://github.com/nicolaigaina/ai-video-captions"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-700 transition-colors hover:text-[#459F94] dark:text-gray-300 dark:hover:text-[#459F94]"
          >
            GitHub
          </a>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2">
          {/* Theme toggle */}
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="cursor-pointer rounded-full p-2 text-gray-700 transition-colors hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
            aria-label="Toggle dark mode"
          >
            {mounted && theme === "dark" ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </button>

          {/* GitHub icon (desktop) */}
          <a
            href="https://github.com/nicolaigaina/ai-video-captions"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden cursor-pointer rounded-full p-2 text-gray-700 transition-colors hover:bg-gray-100 md:inline-flex dark:text-gray-300 dark:hover:bg-gray-800"
            aria-label="GitHub repository"
          >
            <GithubIcon className="h-5 w-5" />
          </a>

          {/* History button (desktop) */}
          <Link
            href="/history"
            className="hidden cursor-pointer items-center gap-1.5 rounded-full bg-[#459F94] px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-[#367d74] md:inline-flex"
          >
            <History className="h-4 w-4" />
            History
          </Link>

          {/* Mobile menu toggle */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="cursor-pointer rounded-full p-2 text-gray-700 transition-colors hover:bg-gray-100 md:hidden dark:text-gray-300 dark:hover:bg-gray-800"
            aria-label="Toggle menu"
          >
            {isMobileMenuOpen ? (
              <X className="h-6 w-6" />
            ) : (
              <Menu className="h-6 w-6" />
            )}
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      <div
        className={`overflow-hidden transition-all duration-300 md:hidden ${
          isMobileMenuOpen ? "max-h-64 opacity-100" : "max-h-0 opacity-0"
        }`}
      >
        <div className="border-t border-gray-200 bg-white/95 px-6 py-4 backdrop-blur-md dark:border-gray-700 dark:bg-black/95">
          <div className="flex flex-col gap-3">
            <Link
              href="/"
              onClick={() => setIsMobileMenuOpen(false)}
              className="text-gray-700 transition-colors hover:text-[#459F94] dark:text-gray-300"
            >
              Home
            </Link>
            <Link
              href="/history"
              onClick={() => setIsMobileMenuOpen(false)}
              className="text-gray-700 transition-colors hover:text-[#459F94] dark:text-gray-300"
            >
              History
            </Link>
            <a
              href="https://github.com/nicolaigaina/ai-video-captions"
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setIsMobileMenuOpen(false)}
              className="flex items-center gap-2 text-gray-700 transition-colors hover:text-[#459F94] dark:text-gray-300"
            >
              <GithubIcon className="h-4 w-4" />
              GitHub
            </a>
          </div>
        </div>
      </div>
    </header>
  );
}
