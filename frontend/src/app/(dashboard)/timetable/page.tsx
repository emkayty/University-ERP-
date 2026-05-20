"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function TimetablePage() {
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Timetable</h1>
      <Card>
        <CardHeader><CardTitle>Weekly Schedule</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500">View your lecture and exam timetable</p>
        </CardContent>
      </Card>
    </div>
  );
}