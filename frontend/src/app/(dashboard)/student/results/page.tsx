"use client";

import { useState, useEffect } from "react";
import { Loader2, CheckCircle, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";

export default function StudentResultsPage() {
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [sessions, setSessions] = useState<any[]>([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [resultsRes, sessionsRes] = await Promise.all([
          api.get("/examinations/results/"),
          api.get("/institutional/sessions/"),
        ]);
        setResults(resultsRes.data.results || []);
        setSessions(sessionsRes.data.results || []);
        if (sessionsRes.data.results?.length) {
          setSelectedSession(sessionsRes.data.results[0].id);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const filteredResults = results.filter(
    (r) => !selectedSession || r.semester?.session?.id === selectedSession
  );

  const cgpa = results.reduce((sum, r) => sum + Number(r.total_score || 0), 0) / (filteredResults.length || 1);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-8 h-8 animate-spin text-brand-primary" />
      </div>
    );
  }

  const isPublished = filteredResults.every((r) => r.is_published);

  return (
    <div className="min-h-screen bg-surface-1 p-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-display font-bold mb-6">My Results</h1>

        {/* Session Selector */}
        <select
          value={selectedSession || ""}
          onChange={(e) => setSelectedSession(e.target.value)}
          className="input mb-6"
        >
          {sessions.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>

        {!isPublished && selectedSession && (
          <div className="mb-6 p-4 bg-yellow-50 rounded-lg">
            <p className="text-yellow-800">
              Results for this semester are not yet published.
            </p>
          </div>
        )}

        {isPublished && (
          <>
            {/* GPA Summary */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="card">
                <div className="card-body text-center">
                  <p className="text-sm text-text-muted">Current GPA</p>
                  <p className="text-3xl font-bold">{cgpa.toFixed(2)}</p>
                </div>
              </div>
              <div className="card">
                <div className="card-body text-center">
                  <p className="text-sm text-text-muted">Total Credits</p>
                  <p className="text-3xl font-bold">
                    {filteredResults.reduce((sum, r) => sum + (r.credit_units || 0), 0)}
                  </p>
                </div>
              </div>
              <div className="card">
                <div className="card-body text-center">
                  <p className="text-sm text-text-muted">Class</p>
                  <p className="text-3xl font-bold">
                    {cgpa >= 4.5 ? "First" : cgpa >= 3.5 ? "Second Upper" : 
                     cgpa >= 2.4 ? "Second Lower" : cgpa >= 1.5 ? "Third" : "Pass"}
                  </p>
                </div>
              </div>
            </div>

            {/* Results Table */}
            <div className="card">
              <div className="overflow-x-auto">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Course</th>
                      <th>Title</th>
                      <th>CA</th>
                      <th>Exam</th>
                      <th>Total</th>
                      <th>Grade</th>
                      <th>Points</th>
                      <th>Units</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredResults.map((r, i) => (
                      <tr key={i}>
                        <td className="font-mono">{r.course_code}</td>
                        <td>{r.course_title}</td>
                        <td>{r.ca_score}</td>
                        <td>{r.exam_score}</td>
                        <td className="font-bold">{r.total_score}</td>
                        <td>
                          <span className={`badge badge-${
                            r.grade === "A" ? "success" :
                            r.grade === "F" ? "danger" : "warning"
                          }`}>
                            {r.grade}
                          </span>
                        </td>
                        <td>{r.grade_points}</td>
                        <td>{r.credit_units}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}