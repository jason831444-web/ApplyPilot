import { ApplicationTable } from "@/components/applications/ApplicationTable";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";

export default function ApplicationsPage() {
  return (
    <ProtectedRoute>
      <ApplicationTable />
    </ProtectedRoute>
  );
}
