"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function ICTAdminDashboard() {
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">ICT Admin Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader><CardTitle>Users</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">1,250</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Online</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-green-600">45</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Tickets</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">12</p></CardContent></Card>
        <Card><CardHeader><CardTitle>API Calls</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">10K</p></CardContent></Card>
      </div>
    </div>
  );
}