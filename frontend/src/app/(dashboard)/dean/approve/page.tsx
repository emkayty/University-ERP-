"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function DeanApprove() {
  const pending = [
    { department: "Computer Science", status: "Pending Dean" },
    { department: "Mathematics", status: "Pending Dean" },
    { department: "Physics", status: "Pending Dean" },
  ];

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Faculty Approval</h1>
      <div className="grid gap-4">
        {pending.map((d, i) => (
          <Card key={i}>
            <CardHeader><CardTitle>{d.department}</CardTitle></CardHeader>
            <CardContent className="flex gap-2">
              <Button>Approve</Button><Button variant="destructive">Reject</Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}