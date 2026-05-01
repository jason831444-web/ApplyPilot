type ScoreItem = {
  label: string;
  value: number;
};

function scoreColor(value: number): string {
  if (value >= 75) {
    return "text-emerald-700";
  }
  if (value >= 55) {
    return "text-amber-700";
  }
  return "text-red-700";
}

export function ScoreCards({ scores }: { scores: ScoreItem[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {scores.map((score) => (
        <div key={score.label} className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{score.label}</p>
          <p className={`mt-2 text-2xl font-semibold ${scoreColor(score.value)}`}>{score.value}</p>
        </div>
      ))}
    </div>
  );
}
