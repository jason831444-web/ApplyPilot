import Link from "next/link";

export default function HomePage() {
  return (
    <section className="space-y-6">
      <div className="space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">ApplyPilot</h1>
        <p className="max-w-2xl text-slate-600">
          A job-fit decision engine for new-grad software engineering candidates.
        </p>
      </div>
      <div className="flex gap-3">
        <Link className="rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white" href="/jobs/new">
          Analyze a Job
        </Link>
        <Link className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium" href="/profile">
          Complete Profile
        </Link>
      </div>
    </section>
  );
}
