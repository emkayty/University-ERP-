"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function LecturerCourses() {
  const courses = [
    { code: "CSC201", title: "Data Structures", students: 45 },
    { code: "CSC202", title: "Algorithms", students: 38 },
    { code: "CSC301", title: "Database Systems", students: 42 },
    { code: "CSC302", title: "Operating Systems", students: 35 },
  ];

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">My Courses</h1>
      <div className="grid gap-4">
        {courses.map((c) => (
          <Card key={c.code}>
            <CardHeader><CardTitle>{c.code} - {c.title}</CardTitle></CardHeader>
            <CardContent><p>{c.students} students enrolled</p></CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}