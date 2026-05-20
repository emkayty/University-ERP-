"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function AttendancePage() {
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Attendance</h1>
      <Card>
        <CardHeader><CardTitle>Your Attendance</CardTitle></CardHeader>
        <CardContent><p className="text-sm">View class attendance records</p></CardContent>
      </Card>
    </div>
  );
}