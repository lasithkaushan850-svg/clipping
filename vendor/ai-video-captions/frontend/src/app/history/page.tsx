import Link from "next/link";
import { Film } from "lucide-react";
import { getCaptionJobs } from "~/actions/captions";
import { CaptionJobCard } from "~/components/caption-job-card";

export const dynamic = "force-dynamic";

export default async function HistoryPage() {
  const jobs = await getCaptionJobs();

  return (
    <section
      className="min-h-screen bg-gray-50 px-6 py-24 dark:bg-gray-950"
      style={{ fontFamily: "var(--font-outfit)" }}
    >
      <div className="mx-auto max-w-6xl">
        {/* Page heading */}
        <div className="mb-10">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Caption History
          </h1>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            All your captioned videos in one place.
          </p>
        </div>

        {jobs.length === 0 ? (
          /* Empty state */
          <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-dashed border-gray-300 py-24 text-center dark:border-gray-700">
            <div className="rounded-full bg-gray-100 p-4 dark:bg-gray-800">
              <Film className="h-8 w-8 text-gray-400 dark:text-gray-500" />
            </div>
            <div>
              <p className="text-base font-semibold text-gray-700 dark:text-gray-300">
                No captions yet
              </p>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Upload a video to get started
              </p>
            </div>
            <Link
              href="/"
              className="mt-2 rounded-full bg-[#459F94] px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#367d74]"
            >
              Upload a video
            </Link>
          </div>
        ) : (
          /* Job grid */
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {jobs.map((job) => (
              <CaptionJobCard key={job.id} job={job} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
