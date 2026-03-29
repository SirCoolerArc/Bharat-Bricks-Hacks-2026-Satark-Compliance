import { NextRequest, NextResponse } from "next/server";
import { MessageAnalysisInput, MessageAnalysisResult } from "@/types";
import { classifyRemark } from "@/lib/scoring/remark-classifier";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const input = body as MessageAnalysisInput;

    if (!input.message || typeof input.message !== "string") {
      return NextResponse.json(
        { error: "message is required and must be a string" },
        { status: 400 }
      );
    }

    const result: MessageAnalysisResult = classifyRemark(input.message);

    return NextResponse.json(result);
  } catch (err) {
    console.error("[analyze-message] error:", err);
    return NextResponse.json(
      { error: "Failed to analyze message" },
      { status: 500 }
    );
  }
}
