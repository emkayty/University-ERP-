"use client";

import { useState, useEffect } from "react";
import { Loader2, TrendingUp, Users, DollarSign, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";

export default function VCDashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const res = await api.get("/mis/vc-stats/");
        setStats(res.data);
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
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-8 h-8 animate-spin text-brand-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-1 p-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-display font-bold mb-6">
          Vice-Chancellor Dashboard
        </h1>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="card">
            <div className="card-body">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Users className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-text-muted">Total Enrolled</p>
                  <p className="text-2xl font-bold">{stats?.total_students?.toLocaleString() || 0}</p>
                  <p className="text-xs text-green-600 flex items-center">
                    <TrendingUp className="w-3 h-3" /> +{stats?.yoy_growth || 0}%
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-body">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <DollarSign className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-text-muted">Revenue (Session)</p>
                  <p className="text-2xl font-bold">₦{(stats?.revenue || 0).toLocaleString()}</p>
                  <p className="text-xs text-text-muted">
                    {stats?.revenue_target_progress || 0}% of target
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-body">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-yellow-600" />
                </div>
                <div>
                  <p className="text-sm text-text-muted">Accreditation Score</p>
                  <p className={`text-2xl font-bold ${
                    stats?.accreditation_score >= 80 ? "text-green-600" :
                    stats?.accreditation_score >= 60 ? "text-yellow-600" : "text-red-600"
                  }`}>
                    {stats?.accreditation_score || 0}%
                  </p>
                  <p className="text-xs text-text-muted">NUC Readiness</p>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-body">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Users className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-text-muted">Academic Staff</p>
                  <p className="text-2xl font-bold">{stats?.total_staff || 0}</p>
                  <p className="text-xs text-red-600">{stats?.staff_vacancies || 0} vacancies</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold">Enrolment Trend</h2>
            </div>
            <div className="card-body h-64 flex items-center justify-center">
              <p className="text-text-muted">Line chart: 5 sessions</p>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold">Revenue by Month</h2>
            </div>
            <div className="card-body h-64 flex items-center justify-center">
              <p className="text-text-muted">Bar chart: current session</p>
            </div>
          </div>
        </div>

        {/* Alerts Panel */}
        <div className="card">
          <div className="card-header">
            <h2 className="font-semibold flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-500" />
              Alerts
            </h2>
          </div>
          <div className="card-body">
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <span className="text-sm">{stats?.alerts?.accreditation_expiring || 0} programmes expiring soon</span>
                <span className="text-xs text-red-600">Action Required</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                <span className="text-sm">{stats?.alerts?.result_backlogs || 0} result backlogs</span>
                <span className="text-xs text-yellow-600">Review</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                <span className="text-sm">{stats?.alerts?.high_risk_students || 0} high-risk students</span>
                <span className="text-xs text-orange-600">Intervention</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}