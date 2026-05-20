"use client";

import { useState, useEffect } from "react";
import { Loader2, CreditCard, Receipt, AlertCircle, CheckCircle } from "lucide-react";
import { api } from "@/lib/api";

export default function FeesDashboardPage() {
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const res = await api.get("/finance/invoices/");
        setInvoices(res.data.results || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const total = invoices.reduce((sum, inv) => sum + Number(inv.total_amount || 0), 0);
  const paid = invoices.reduce((sum, inv) => sum + Number(inv.amount_paid || 0), 0);
  const outstanding = total - paid;

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
        <h1 className="text-2xl font-display font-bold mb-6">My Fees</h1>

        {/* Summary Cards */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="card">
            <div className="card-body">
              <p className="text-sm text-text-muted">Total Invoice</p>
              <p className="text-2xl font-bold">₦{total.toLocaleString()}</p>
            </div>
          </div>
          
          <div className="card">
            <div className="card-body">
              <p className="text-sm text-text-muted">Amount Paid</p>
              <p className="text-2xl font-bold text-success">₦{paid.toLocaleString()}</p>
            </div>
          </div>
          
          <div className="card">
            <div className="card-body">
              <p className="text-sm text-text-muted">Outstanding</p>
              <p className="text-2xl font-bold text-danger">₦{outstanding.toLocaleString()}</p>
            </div>
          </div>
        </div>

        {/* Invoices */}
        <div className="card">
          <div className="card-header">
            <h2 className="font-semibold">Invoices</h2>
          </div>
          <div className="divide-y divide-surface-2">
            {invoices.map((inv) => (
              <div key={inv.id} className="p-4 flex items-center justify-between">
                <div>
                  <p className="font-medium">{inv.session?.name}</p>
                  <p className="text-sm text-text-muted">
                    ₦{Number(inv.total_amount).toLocaleString()} • {inv.state}
                  </p>
                </div>
                
                <div className="flex items-center gap-2">
                  {inv.state === "fully_paid" ? (
                    <span className="badge badge-success">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Paid
                    </span>
                  ) : (
                    <button
                      onClick={() => window.location.href = `/student/fees/pay/${inv.id}`}
                      className="btn btn-primary btn-sm"
                    >
                      <CreditCard className="w-4 h-4" />
                      Pay Now
                    </button>
                  )}
                </div>
              </div>
            ))}
            
            {invoices.length === 0 && (
              <div className="p-8 text-center text-text-muted">
                No invoices found
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}