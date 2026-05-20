"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function LibraryPage() {
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Library</h1>
      <Card><CardHeader><CardTitle>Borrow Books</CardTitle></CardHeader><CardContent><p>Search and borrow library books</p></CardContent></Card>
    </div>
  );
}