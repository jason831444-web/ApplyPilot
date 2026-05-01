import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { JobDetailView } from "@/components/jobs/JobDetailView";

export default async function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  return (
    <ProtectedRoute>
      <JobDetailView jobId={id} />
    </ProtectedRoute>
  );
}
