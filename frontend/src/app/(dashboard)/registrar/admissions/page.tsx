"use client";

import { useState, useEffect } from "react";
import { Loader2, Users, FileText, CheckCircle, XCircle, Download, Filter } from "lucide-react";
import { api } from "@/lib/api";

export default function AdmissionsPage() {
  const [applications, setApplications] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    const loadData = async () => {
      try {
        const [appsRes, statsRes] = await Promise.all([
          api.get("/admissions/applications/", { params: { page_size: 50 } }),
          api.get("/admissions/applications/stats/"),
        ]);
        setApplications(appsRes.data.results || []);
        setStats(statsRes.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-brand-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-1 p-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-display font-bold mb-6">Admissions Dashboard</h1>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="card">
              <div className="card-body flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <FileText className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.total}</p>
                  <p className="text-sm text-text-muted">Total Applications</p>
                </div>
              </div>
            </div>
            
            <div className="card">
              <div className="card-body flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.jamb_verified}</p>
                  <p className="text-sm text-text-muted">JAMB Verified</p>
                </div>
              </div>
            </div>
            
            <div className="card">
              <div className="card-body flex items-center gap-3">
                <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <Users className="w-5 h-5 text-yellow-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.offered}</p>
                  <p className="text-sm text-text-muted">Offers Sent</p>
                </div>
              </div>
            </div>
            
            <div className="card">
              <div className="card-body flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-purple-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.accepted}</p>
                  <p className="text-sm text-text-muted">Accepted</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filter */}
        <div className="flex gap-2 mb-4">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="input"
          >
            <option value="all">All Status</option>
            <option value="submitted">Submitted</option>
            <option value="jamb_verified">JAMB Verified</option>
            <option value="offered">Offered</option>
            <option value="accepted">Accepted</option>
          </select>
          
          <button className="btn btn-outline">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>

        {/* Applications Table */}
        <div className="card">
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>JAMB Reg No</th>
                  <th>Programme</th>
                  <th>JAMB Score</th>
                  <th>Aggregate</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {applications
                  .filter((a) => filter === "all" || a.state === filter)
                  .map((app) => (
                    <tr key={app.id}>
                      <td className="font-mono">{app.jamb_reg_no}</td>
                      <td>{app.programme_choice_1?.name}</td>
                      <td>{app.jamb_score || "-"}</td>
                      <td>{app.aggregate_score || "-"}</td>
                      <td>
                        <span className={`badge badge-${
                          app.state === "offered" ? "success" :
                          app.state === "submitted" ? "info" :
                          app.state === "accepted" ? "success" :
                          "warning"
                        }`}>
                          {app.state}
                        </span>
                      </td>
                      <td>
                        <button className="btn btn-ghost text-sm">
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}