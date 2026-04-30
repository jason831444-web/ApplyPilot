import { ProtectedRoute } from "@/components/auth/ProtectedRoute";

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <section className="space-y-2">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-slate-600">Job-search insights and charts will be implemented later.</p>
      </section>
    </ProtectedRoute>
  );
}
