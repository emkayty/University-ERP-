"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function DeanDashboard() {
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Dean Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Departments</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">5</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Staff</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">45</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Students</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">800</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Pending</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">8</p></CardContent></Card>
      </div>
      <Card>
        <CardHeader><CardTitle>Quick Actions</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          <Button className="w-full" variant="outline" onClick={() => window.location.href = "/dean/approve"}>Approve Results</Button>
        </CardContent>
      </Card>
    </div>
  );
}