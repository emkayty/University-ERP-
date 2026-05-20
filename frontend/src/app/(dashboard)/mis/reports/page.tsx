"use client";

import { useState } from "react";
import { FileText, Download } from "lucide-react";

export default function ReportsPage() {
  const categories = [
    { id: "admissions", name: "Admissions", count: 5 },
    { id: "enrolment", name: "Enrolment", count: 8 },
    { id: "financial", name: "Financial", count: 12 },
    { id: "academic", name: "Academic", count: 10 },
    { id: "hr", name: "HR", count: 6 },
    { id: "nysc", name: "NYSC", count: 3 },
  ];

  const [selectedCategory, setSelectedCategory] = useState("admissions");

  return (
    <div className="min-h-screen bg-surface-1 p-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-display font-bold mb-6">MIS Reports</h1>

        <div className="flex gap-4 mb-6">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-4 py-2 rounded-lg ${
                selectedCategory === cat.id
                  ? "bg-brand-primary text-white"
                  : "bg-white text-text-secondary"
              }`}
            >
              {cat.name}
            </button>
          ))}
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="font-semibold capitalize">{selectedCategory} Reports</h2>
          </div>
          <div className="divide-y">
            {[
              { title: "Admission Statistics", description: "Applications, offers, acceptances by session", date: "2025-01-15" },
              { title: "JAMB Score Distribution", description: "Histogram of JAMB scores", date: "2025-01-10" },
              { title: "Programme Demand Analysis", description: "First choice preferences by programme", date: "2025-01-05" },
            ].map((report, i) => (
              <div key={i} className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium">{report.title}</p>
                    <p className="text-sm text-text-muted">{report.description}</p>
                    <p className="text-xs text-text-muted">{report.date}</p>
                  </div>
                </div>
                <button className="btn btn-outline btn-sm">
                  <Download className="w-4 h-4" />
                  Export
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}