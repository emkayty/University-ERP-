"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function BursarFees() {
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Fee Management</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card><CardHeader><CardTitle>Today</CardTitle></CardHeader><CardContent><p className="text-xl font-bold">₦2,500,000</p><p className="text-sm">Collections</p></CardContent></Card>
        <Card><CardHeader><CardTitle>This Week</CardTitle></CardHeader><CardContent><p className="text-xl font-bold">₦15,000,000</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Outstanding</CardTitle></CardHeader><CardContent><p className="text-xl font-bold text-red-600">₦45,000,000</p></CardContent></Card>
      </div>
    </div>
  );
}