import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { JobDetailView } from "@/components/jobs/JobDetailView";

export default function JobDetailPage({ params }: { params: { id: string } }) {
  return (
    <ProtectedRoute>
      <JobDetailView jobId={params.id} />
    </ProtectedRoute>
  );
}
