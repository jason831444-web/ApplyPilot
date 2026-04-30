import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { JobsList } from "@/components/jobs/JobsList";

export default function JobsPage() {
  return (
    <ProtectedRoute>
      <JobsList />
    </ProtectedRoute>
  );
}
