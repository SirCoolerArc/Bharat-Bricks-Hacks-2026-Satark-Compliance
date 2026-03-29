import { NextResponse } from "next/server";
import { fetchDashboardData } from "@/lib/databricks/dashboard";

export async function GET() {
  try {
    const data = await fetchDashboardData();
    return NextResponse.json(data);
  } catch (err) {
    console.error("[api/dashboard] error:", err);
    return NextResponse.json(
      { error: "Failed to fetch dashboard data" },
      { status: 500 }
    );
  }
}
