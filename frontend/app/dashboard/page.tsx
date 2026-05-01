import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { DashboardSummary } from "@/components/dashboard/DashboardSummary";

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardSummary />
    </ProtectedRoute>
  );
}
