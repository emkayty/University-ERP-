"use client";

import { useState, useEffect, useCallback } from "react";
import { Loader2, Save, AlertTriangle, CheckCircle } from "lucide-react";
import { api } from "@/lib/api";

export default function ScoreEntryPage({ params }: { params: { offeringId: string } }) {
  const [scores, setScores] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const batchState = "draft";

  useEffect(() => {
    const loadScores = async () => {
      try {
        const res = await api.get(`/courses/offerings/${params.offeringId}/scores/`);
        setScores(res.data.results || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadScores();
  }, [params.offeringId]);

  const updateScore = useCallback((studentId: string, field: string, value: string) => {
    setScores(scores.map((s) => 
      s.student.id === studentId 
        ? { ...s, [field]: value }
        : s
    ));
  }, [scores]);

  const handleSave = useCallback(async () => {
    setSaving(true);
    setError(null);
    
    const payload = scores.map((s) => ({
      student_id: s.student.id,
      ca_score: s.ca_score,
      exam_score: s.exam_score,
    }));
    
    try {
      await api.post(`/examinations/scores/`, {
        offering_id: params.offeringId,
        scores: payload,
      });
      setSuccess("Scores saved successfully");
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to save scores");
    } finally {
      setSaving(false);
    }
  }, [scores, params.offeringId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-8 h-8 animate-spin text-brand-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-1 p-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-display font-bold mb-6">Score Entry</h1>

        {error && (
          <div className="mb-4 p-4 bg-red-50 rounded-lg">
            <span className="text-danger">{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-4 p-4 bg-green-50 rounded-lg">
            <span className="text-success">{success}</span>
          </div>
        )}

        <div className="card overflow-hidden">
          <table className="table">
            <thead>
              <tr>
                <th>Matric</th>
                <th>Name</th>
                <th>CA</th>
                <th>Exam</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {scores.map((score) => {
                const ca = parseFloat(score.ca_score || "0") || 0;
                const ex = parseFloat(score.exam_score || "0") || 0;
                return (
                  <tr key={score.student.id}>
                    <td className="font-mono">{score.student.matric_number}</td>
                    <td>{score.student.first_name}</td>
                    <td>
                      <input
                        type="number"
                        value={score.ca_score || ""}
                        onChange={(e) => updateScore(score.student.id, "ca_score", e.target.value)}
                        className="input w-20"
                        disabled={batchState !== "draft"}
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        value={score.exam_score || ""}
                        onChange={(e) => updateScore(score.student.id, "exam_score", e.target.value)}
                        className="input w-20"
                        disabled={batchState !== "draft"}
                      />
                    </td>
                    <td>{ca + ex}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {batchState === "draft" && (
          <div className="mt-4 flex justify-end gap-3">
            <button onClick={handleSave} disabled={saving} className="btn btn-primary">
              {saving ? <Loader2 className="w-5 h-5" /> : "Save"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}