import { ButtonLink } from "./Button";

export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return <p className="rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">{label}</p>;
}

export function ErrorState({ message }: { message: string }) {
  return <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{message || "Something went wrong."}</p>;
}

export function EmptyState({
  title,
  description,
  actionHref,
  actionLabel,
}: {
  title: string;
  description: string;
  actionHref?: string;
  actionLabel?: string;
}) {
  return (
    <div className="rounded-md border border-dashed border-slate-300 bg-white px-4 py-8">
      <h2 className="text-base font-semibold text-slate-950">{title}</h2>
      <p className="mt-1 max-w-2xl text-sm text-slate-600">{description}</p>
      {actionHref && actionLabel ? (
        <ButtonLink className="mt-4" href={actionHref}>
          {actionLabel}
        </ButtonLink>
      ) : null}
    </div>
  );
}
