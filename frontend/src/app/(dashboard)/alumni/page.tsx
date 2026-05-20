"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function AlumniPage() {
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Alumni</h1>
      <Card><CardHeader><CardTitle>Directory</CardTitle></CardHeader><CardContent><p>Search alumni directory</p></CardContent></Card>
    </div>
  );
}