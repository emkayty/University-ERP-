"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function HODApprove() {
  const results = [
    { course: "CSC201", lecturer: "Dr. Ade", status: "Pending HOD" },
    { course: "CSC202", lecturer: "Prof. Bello", status: "Pending HOD" },
  ];

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Approve Results</h1>
      <div className="grid gap-4">
        {results.map((r) => (
          <Card key={r.course}>
            <CardHeader><CardTitle>{r.course}</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <p>{r.lecturer}</p>
              <div className="flex gap-2">
                <Button>Approve</Button>
                <Button variant="destructive">Reject</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}