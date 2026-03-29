import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const { table } = await req.json();
  
  if (!table) {
    return NextResponse.json({ error: "Table parameter is required" }, { status: 400 });
  }

  try {
    // Calling the local FastAPI backend instead of the remote database
    const response = await fetch("http://127.0.0.1:8000/api/analytics", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ table }),
      cache: "no-store",
    });

    if (!response.ok) {
        throw new Error(`FastAPI backend error: ${response.statusText}`);
    }

    const result = await response.json();
    return NextResponse.json({ data: result.data || [] });
  } catch (error) {
    console.error("Local Analytics API error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    );
  }
}
