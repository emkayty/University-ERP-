"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function HealthPage() {
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Health Centre</h1>
      <Card><CardHeader><CardTitle>Book Appointment</CardTitle></CardHeader><CardContent><p>Book appointment with health centre</p></CardContent></Card>
    </div>
  );
}