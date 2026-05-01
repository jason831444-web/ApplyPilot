"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { formatTitle } from "@/lib/format";
import type { DistributionItem } from "@/lib/types";

const COLORS = ["#0f766e", "#d97706", "#0369a1", "#dc2626", "#64748b"];

export function RecommendationChart({ title, data }: { title: string; data: DistributionItem[] }) {
  const chartData = data.map((item) => ({ ...item, name: formatTitle(item.label) }));

  return (
    <section className="rounded-md border border-slate-200 bg-white p-5">
      <h2 className="text-base font-semibold">{title}</h2>
      {chartData.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No data yet.</p>
      ) : (
        <div className="mt-4 grid gap-4 md:grid-cols-[minmax(0,1fr)_180px]">
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={chartData} dataKey="count" nameKey="name" innerRadius={45} outerRadius={80} paddingAngle={2}>
                  {chartData.map((item, index) => (
                    <Cell key={item.label} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <ul className="space-y-2 self-center text-sm text-slate-700">
            {chartData.map((item, index) => (
              <li key={item.label} className="flex items-center justify-between gap-3">
                <span className="inline-flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                  {item.name}
                </span>
                <span className="font-semibold text-slate-950">{item.count}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
