"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatTitle } from "@/lib/format";
import type { DistributionItem } from "@/lib/types";

export function StatusChart({ title, data }: { title: string; data: DistributionItem[] }) {
  const chartData = data.map((item) => ({ ...item, name: formatTitle(item.label) }));

  return (
    <section className="rounded-md border border-slate-200 bg-white p-5">
      <h2 className="text-base font-semibold">{title}</h2>
      {chartData.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No data yet.</p>
      ) : (
        <div className="mt-4 h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ left: -20, right: 10, top: 10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} interval={0} angle={-20} textAnchor="end" height={60} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#0f172a" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
