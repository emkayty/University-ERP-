"use client";

import { useState, useEffect } from "react";
import { Loader2, DollarSign, Users, CreditCard, TrendingUp } from "lucide-react";
import { api } from "@/lib/api";

export default function BursarDashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [payments, setPayments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [statsRes, paymentsRes] = await Promise.all([
          api.get("/finance/stats/"),
          api.get("/finance/payments/", { params: { page_size: 20 } }),
        ]);
        setStats(statsRes.data);
        setPayments(paymentsRes.data.results || []);
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
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-display font-bold mb-6">
          Bursar Dashboard
        </h1>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="card">
            <div className="card-body flex items-center gap-3">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <DollarSign className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  ₦{(stats?.today_collections || 0).toLocaleString()}
                </p>
                <p className="text-sm text-text-muted">Today's Collections</p>
              </div>
            </div>
          </div>
          
          <div className="card">
            <div className="card-body flex items-center gap-3">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  ₦{(stats?.monthly_collections || 0).toLocaleString()}
                </p>
                <p className="text-sm text-text-muted">This Month</p>
              </div>
            </div>
          </div>
          
          <div className="card">
            <div className="card-body flex items-center gap-3">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                <Users className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {stats?.outstanding_debtors || 0}
                </p>
                <p className="text-sm text-text-muted">Outstanding Debtors</p>
              </div>
            </div>
          </div>
          
          <div className="card">
            <div className="card-body flex items-center gap-3">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <CreditCard className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {stats?.payment_count || 0}
                </p>
                <p className="text-sm text-text-muted">Total Payments</p>
              </div>
            </div>
          </div>
        </div>

        {/* Revenue by Payment Method */}
        <div className="card mb-6">
          <div className="card-header">
            <h2 className="font-semibold">Revenue by Payment Method</h2>
          </div>
          <div className="card-body">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(stats?.by_method || {}).map(([method, amount]) => (
                <div key={method} className="text-center">
                  <p className="text-2xl font-bold">₦{(amount as number).toLocaleString()}</p>
                  <p className="text-sm text-text-muted capitalize">{method}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Payments */}
        <div className="card">
          <div className="card-header">
            <h2 className="font-semibold">Recent Payments</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Matric No</th>
                  <th>Amount</th>
                  <th>Gateway</th>
                  <th>Status</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {payments.map((payment) => (
                  <tr key={payment.id}>
                    <td className="font-mono">
                      {payment.invoice?.student?.matric_number}
                    </td>
                    <td>₦{Number(payment.amount).toLocaleString()}</td>
                    <td className="capitalize">{payment.gateway}</td>
                    <td>
                      <span className={`badge badge-${
                        payment.status === "successful" ? "success" :
                        payment.status === "pending" ? "warning" : "danger"
                      }`}>
                        {payment.status}
                      </span>
                    </td>
                    <td>{new Date(payment.created_at).toLocaleDateString()}</td>
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