"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { FileText, CheckCircle, Clock, AlertCircle, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

const STATUS_ORDER = [
  { key: "draft", label: "Draft" },
  { key: "submitted", label: "Submitted" },
  { key: "jamb_verified", label: "JAMB Verified" },
  { key: "offered", label: "Offered" },
  { key: "accepted", label: "Accepted" },
  { key: "cleared", label: "Cleared" },
  { key: "matriculated", label: "Matriculated" },
];

export default function StatusPage() {
  const router = useRouter();
  const [application, setApplication] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const res = await api.get("/admissions/applications/", {
          params: { page_size: 1 },
        });
        setApplication(res.data.results?.[0]);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadStatus();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-brand-primary" />
      </div>
    );
  }

  const currentIndex = application
    ? STATUS_ORDER.findIndex((s) => s.key === application.state)
    : 0;

  return (
    <div className="min-h-screen bg-surface-1 p-4">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-display font-bold mb-6">Application Status</h1>

        {/* Timeline */}
        <div className="card">
          <div className="card-body">
            {STATUS_ORDER.map((status, index) => {
              const isComplete = index < currentIndex;
              const isCurrent = index === currentIndex;
              const isPending = index > currentIndex;

              return (
                <div key={status.key} className="flex items-center gap-4 py-4">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      isComplete
                        ? "bg-green-500 text-white"
                        : isCurrent
                        ? "bg-blue-500 text-white"
                        : "bg-surface-2 text-text-muted"
                    }`}
                  >
                    {isComplete ? (
                      <CheckCircle className="w-6 h-6" />
                    ) : isCurrent ? (
                      <Clock className="w-6 h-6" />
                    ) : (
                      index + 1
                    )}
                  </div>
                  <div className="flex-1">
                    <p
                      className={`font-medium ${
                        isPending ? "text-text-muted" : "text-text-primary"
                      }`}
                    >
                      {status.label}
                    </p>
                    {isCurrent && application && (
                      <p className="text-sm text-text-muted">
                        Updated: {new Date(application.updated_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Application Details */}
        {application && (
          <div className="card mt-4">
            <div className="card-body">
              <h2 className="text-lg font-semibold mb-4">Application Details</h2>
              <dl className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm text-text-muted">JAMB Reg No</dt>
                  <dd className="font-mono">{application.jamb_reg_no}</dd>
                </div>
                {application.jamb_score && (
                  <div>
                    <dt className="text-sm text-text-muted">JAMB Score</dt>
                    <dd>{application.jamb_score}</dd>
                  </div>
                )}
                {application.aggregate_score && (
                  <div>
                    <dt className="text-sm text-text-muted">Aggregate</dt>
                    <dd>{application.aggregate_score}</dd>
                  </div>
                )}
              </dl>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}