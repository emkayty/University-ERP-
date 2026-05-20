"use client";

import { useState, useEffect } from "react";
import { Loader2, Plus, Minus, AlertTriangle, Check, X } from "lucide-react";
import { api } from "@/lib/api";

export default function CourseRegistrationPage() {
  const [courses, setCourses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string[]>([]);
  const [registering, setRegistering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const maxCredits = 24;

  useEffect(() => {
    const loadCourses = async () => {
      try {
        const res = await api.get("/courses/offerings/", {
          params: { page_size: 100 },
        });
        setCourses(res.data.results || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadCourses();
  }, []);

  const totalCredits = selected.reduce((sum, id) => {
    const course = courses.find((c) => c.id === id);
    return sum + (course?.credit_units || 0);
  }, 0);

  const toggleCourse = (id: string) => {
    if (selected.includes(id)) {
      setSelected(selected.filter((s) => s !== id));
    } else {
      if (totalCredits + (courses.find((c) => c.id === id)?.credit_units || 0) <= maxCredits) {
        setSelected([...selected, id]);
      } else {
        setError(`Maximum ${maxCredits} credits exceeded`);
      }
    }
  };

  const handleRegister = async () => {
    setRegistering(true);
    setError(null);
    try {
      await api.post("/courses/register/", {
        offering_ids: selected,
      });
      setSuccess("Courses registered successfully!");
      setSelected([]);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Registration failed");
    } finally {
      setRegistering(false);
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
        <h1 className="text-2xl font-display font-bold mb-6">
          Course Registration
        </h1>

        {/* Error/Success Messages */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-danger" />
            <span className="text-danger">{error}</span>
            <button onClick={() => setError(null)} className="ml-auto">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
        
        {success && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2">
            <Check className="w-5 h-5 text-success" />
            <span className="text-success">{success}</span>
          </div>
        )}

        {/* Course List */}
        <div className="space-y-3 mb-24">
          {courses.map((offering) => {
            const isSelected = selected.includes(offering.id);
            const course = offering.course;
            
            return (
              <div
                key={offering.id}
                className={`card cursor-pointer transition-all ${
                  isSelected ? "ring-2 ring-brand-primary" : ""
                }`}
                onClick={() => toggleCourse(offering.id)}
              >
                <div className="card-body flex items-center gap-4">
                  <div
                    className={`w-6 h-6 rounded border flex items-center justify-center ${
                      isSelected
                        ? "bg-brand-primary border-brand-primary"
                        : "border-surface-2"
                    }`}
                  >
                    {isSelected && <Check className="w-4 h-4 text-white" />}
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-medium">{course?.code}</span>
                      <span className="badge badge-info">{course?.credit_units} units</span>
                      {course?.level === 100 && (
                        <span className="badge badge-warning">100 Level</span>
                      )}
                    </div>
                    <p className="text-text-secondary">{course?.title}</p>
                    <p className="text-sm text-text-muted">
                      {offering.lecturer?.email || "TBA"} • {offering.current_enrolment}/{offering.max_enrolment} enrolled
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Sticky Footer */}
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-surface-2 p-4">
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <div>
              <p className="text-sm text-text-muted">Total Credits</p>
              <p className="text-2xl font-bold">
                {totalCredits}
                <span className="text-text-muted text-base font-normal">/{maxCredits}</span>
              </p>
              {totalCredits > maxCredits - 3 && (
                <p className="text-sm text-warning">
                  Approaching credit limit
                </p>
              )}
            </div>
            
            <button
              onClick={handleRegister}
              disabled={selected.length === 0 || registering}
              className="btn btn-primary"
            >
              {registering ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <Plus className="w-5 h-5" />
                  Register Courses
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}