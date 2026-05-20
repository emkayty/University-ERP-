"use client";

import { useState, useEffect } from "react";
import { Loader2, FileText, Send, Check } from "lucide-react";
import { api } from "@/lib/api";

export default function TranscriptRequestPage() {
  const [requests, setRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const loadRequests = async () => {
      try {
        const res = await api.get("/records/transcript-requests/");
        setRequests(res.data.results || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadRequests();
  }, []);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitting(true);
    
    const formData = new FormData(e.currentTarget);
    
    try {
      await api.post("/records/transcript-requests/", {
        request_type: formData.get("request_type"),
        delivery_method: formData.get("delivery_method"),
        destination: {
          type: formData.get("dest_type"),
          email: formData.get("email"),
          name: formData.get("institution_name"),
        },
        purpose: formData.get("purpose"),
      });
      setShowForm(false);
    } catch (e) {
      console.error(e);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-8 h-8 animate-spin text-brand-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-1 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-display font-bold">Transcript Requests</h1>
          <button onClick={() => setShowForm(true)} className="btn btn-primary">
            New Request
          </button>
        </div>

        {showForm && (
          <div className="card mb-6">
            <div className="card-header">
              <h2 className="font-semibold">Request Transcript</h2>
            </div>
            <form onSubmit={handleSubmit} className="card-body space-y-4">
              <div>
                <label className="input-label">Request Type</label>
                <select name="request_type" className="input" required>
                  <option value="official">Official — Senate Authenticated</option>
                  <option value="student_copy">Student Copy — Watermarked</option>
                  <option value="statement_of_results">Statement of Results</option>
                  <option value="attestation">Attestation Letter</option>
                </select>
              </div>
              
              <div>
                <label className="input-label">Delivery Method</label>
                <select name="delivery_method" className="input" required>
                  <option value="digital">Digital — Encrypted Email</option>
                  <option value="courier">Courier Dispatch</option>
                  <option value="pickup">Registry Pickup</option>
                </select>
              </div>
              
              <div>
                <label className="input-label">Destination Type</label>
                <select name="dest_type" className="input" required>
                  <option value="university">University/Institution</option>
                  <option value="employer">Employer</option>
                  <option value="personal">Personal</option>
                </select>
              </div>
              
              <div>
                <label className="input-label">Email</label>
                <input name="email" type="email" className="input" required />
              </div>
              
              <div>
                <label className="input-label">Institution Name</label>
                <input name="institution_name" className="input" />
              </div>
              
              <div>
                <label className="input-label">Purpose</label>
                <textarea name="purpose" className="input" rows={2} />
              </div>
              
              <div className="flex gap-2">
                <button type="submit" disabled={submitting} className="btn btn-primary">
                  {submitting ? <Loader2 className="w-5 h-5 animate-spin" /> : "Submit Request"}
                </button>
                <button type="button" onClick={() => setShowForm(false)} className="btn btn-outline">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        <div className="card">
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Destination</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {requests.map((req) => (
                  <tr key={req.id}>
                    <td>{new Date(req.created_at).toLocaleDateString()}</td>
                    <td>{req.request_type}</td>
                    <td>{req.destination?.email || req.destination?.name}</td>
                    <td>
                      <span className={`badge badge-${
                        req.state === "delivered" ? "success" :
                        req.state === "generated" ? "info" :
                        req.state === "processing" ? "warning" : "default"
                      }`}>
                        {req.state}
                      </span>
                    </td>
                  </tr>
                ))}
                {requests.length === 0 && (
                  <tr>
                    <td colSpan={4} className="text-center text-text-muted py-8">
                      No transcript requests
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}