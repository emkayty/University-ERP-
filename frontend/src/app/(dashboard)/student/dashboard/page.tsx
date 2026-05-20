"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface StudentDashboardProps {
  user: {
    firstName: string;
    lastName: string;
    matricNumber: string;
    programme: string;
    level: number;
    cgpa: number;
  };
  stats: {
    registeredCourses: number;
    pendingFees: number;
    attendancePercent: number;
  };
}

export default function StudentDashboard({ user, stats }: StudentDashboardProps) {
  const router = useRouter();

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Welcome, {user.firstName}</h1>
          <p className="text-gray-500">{user.matricNumber} - {user.programme}</p>
        </div>
        <Badge variant={stats.attendancePercent >= 75 ? "default" : "destructive"}>
          Attendance: {stats.attendancePercent}%
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push("/student/registration")}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Courses</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{stats.registeredCourses}</p>
            <p className="text-xs text-gray-500">Registered</p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push("/student/results")}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">CGPA</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{user.cgpa.toFixed(2)}</p>
            <p className="text-xs text-gray-500">Level {user.level}</p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push("/student/fees")}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Fees</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">₦{stats.pendingFees.toLocaleString()}</p>
            <p className="text-xs text-gray-500">Pending</p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Messages</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">0</p>
            <p className="text-xs text-gray-500">Unread</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button className="w-full" variant="outline" onClick={() => router.push("/student/registration")}>
              Course Registration
            </Button>
            <Button className="w-full" variant="outline" onClick={() => router.push("/student/results")}>
              View Results
            </Button>
            <Button className="w-full" variant="outline" onClick={() => router.push("/student/fees")}>
              Pay Fees
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Upcoming</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500">No upcoming events</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}