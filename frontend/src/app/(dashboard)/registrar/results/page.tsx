"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function RegistrarResults() {
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Result Management</h1>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader><CardTitle>Pending</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">12</p></CardContent></Card>
        <Card><CardHeader><CardTitle>HOD</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">5</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Dean</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">3</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Senate</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">8</p></CardContent></Card>
      </div>
    </div>
  );
}