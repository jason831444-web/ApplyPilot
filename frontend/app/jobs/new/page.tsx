import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { NewJobForm } from "@/components/jobs/NewJobForm";

export default function NewJobPage() {
  return (
    <ProtectedRoute>
      <NewJobForm />
    </ProtectedRoute>
  );
}
