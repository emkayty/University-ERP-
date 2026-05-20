"use client";

import { useState, useEffect } from "react";
import { Loader2, CheckCircle, XCircle } from "lucide-react";
import { api } from "@/lib/api";

export default function VerifyPage({ params }: { params: { code: string } }) {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const verify = async () => {
      try {
        const res = await api.get(`/records/verify/${params.code}/`);
        setResult(res.data);
      } catch (e: any) {
        setError(e.response?.data?.detail || "Verification failed");
      } finally {
        setLoading(false);
      }
    };
    verify();
  }, [params.code]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-1">
        <Loader2 className="w-8 h-8 animate-spin text-brand-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-1 p-4">
        <div className="card max-w-md">
          <div className="card-body text-center">
            <XCircle className="w-16 h-16 text-danger mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-danger mb-2">Verification Failed</h1>
            <p className="text-text-muted">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-1 p-4">
      <div className="card max-w-lg w-full">
        <div className="card-body">
          <div className="text-center mb-6">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-12 h-12 text-success" />
            </div>
            <h1 className="text-2xl font-bold">This Transcript is Authentic</h1>
            <p className="text-text-muted">Verified by University Records Office</p>
          </div>

          <div className="bg-surface-2 rounded-lg p-4 space-y-3">
            <div className="flex justify-between">
              <span className="text-text-muted">Student Name</span>
              <span className="font-medium">{result?.student_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Matric Number</span>
              <span className="font-medium font-mono">{result?.matric_number}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Programme</span>
              <span className="font-medium">{result?.programme}</span>
            </div>
          </div>

          <p className="text-center text-sm text-text-muted mt-6">
            Verification ID: {params.code}
          </p>
        </div>
      </div>
    </div>
  );
}