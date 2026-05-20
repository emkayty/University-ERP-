"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function HostelPage() {
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Hostel</h1>
      <Card><CardHeader><CardTitle>Apply for Hostel</CardTitle></CardHeader><CardContent><p className="text-sm">Submit hostel application</p></CardContent></Card>
    </div>
  );
}