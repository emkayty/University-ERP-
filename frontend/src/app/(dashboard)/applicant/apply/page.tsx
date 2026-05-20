"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Loader2, FileText, CheckCircle, ChevronRight } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api } from "@/lib/api";

const STEPS = [
  { id: 1, title: "Personal" },
  { id: 2, title: "Academic" },
  { id: 3, title: "JAMB" },
  { id: 4, title: "Programme" },
  { id: 5, title: "Documents" },
];

const schema = z.object({
  first_name: z.string().min(1),
  last_name: z.string().min(1),
  phone: z.string().min(10),
  date_of_birth: z.string().min(1),
  gender: z.enum(["M", "F"]),
  state_of_origin: z.string().min(1),
  jamb_reg_no: z.string().min(10),
  programme_choice_1: z.string().min(1),
});

export default function ApplyPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [programmes, setProgrammes] = useState<any[]>([]);

  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
  });

  const onSubmit = useCallback(async (data: any) => {
    setLoading(true);
    try {
      await api.post("/admissions/applications/", data);
      router.push("/applicant/status");
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-surface-1 p-4">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-display font-bold mb-6">Admission Application</h1>
        
        {/* Progress */}
        <div className="mb-8 flex justify-between">
          {STEPS.map((s) => (
            <div key={s.id} className={`text-sm ${step >= s.id ? "text-brand-primary" : "text-text-muted"}`}>
              {step > s.id ? "✓" : s.id}
            </div>
          ))}
        </div>
        
        <div className="h-2 bg-surface-2 rounded-full mb-6">
          <div className="h-full bg-brand-primary" style={{ width: `${(step / STEPS.length) * 100}%` }} />
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="card">
          <div className="card-body">
            {step === 1 && (
              <>
                <h2 className="text-lg font-semibold mb-4">Personal Information</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="input-label">First Name</label>
                    <input {...register("first_name")} className="input" />
                  </div>
                  <div>
                    <label className="input-label">Last Name</label>
                    <input {...register("last_name")} className="input" />
                  </div>
                </div>
              </>
            )}
            
            {step === 3 && (
              <>
                <h2 className="text-lg font-semibold mb-4">JAMB Details</h2>
                <div>
                  <label className="input-label">JAMB Registration Number</label>
                  <input {...register("jamb_reg_no")} className="input font-mono" />
                </div>
              </>
            )}
          </div>
          
          <div className="card-footer flex justify-between">
            <button type="button" onClick={() => setStep(Math.max(1, step - 1))} 
              className="btn btn-outline" disabled={step === 1}>
              Previous
            </button>
            
            {step < STEPS.length ? (
              <button type="button" onClick={() => setStep(step + 1)} className="btn btn-primary">
                Next
              </button>
            ) : (
              <button type="submit" disabled={loading} className="btn btn-primary">
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Submit"}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}