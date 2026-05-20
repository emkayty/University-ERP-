"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function VAccreditation() {
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Accreditation Status</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card><CardHeader><CardTitle>Programmes</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">24</p><p className="text-sm gray">Total</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Accredited</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-green-600">18</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Pending</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold text-yellow-600">6</p></CardContent></Card>
      </div>
    </div>
  );
}