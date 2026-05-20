"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function DisciplinePage() {
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Discipline</h1>
      <Card><CardHeader><CardTitle>Discipline Records</CardTitle></CardHeader><CardContent><p>View discipline case history</p></CardContent></Card>
    </div>
  );
}