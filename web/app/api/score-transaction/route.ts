import { NextRequest, NextResponse } from "next/server";
import { TransactionInput, TransactionScore, RiskLevel } from "@/types";
import { buildFeatureVector, generateFlags } from "@/lib/scoring/feature-builder";
import { classifyRemark } from "@/lib/scoring/remark-classifier";

const MODEL_API_URL = process.env.MODEL_API_URL || 'http://localhost:8000';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const input = body as TransactionInput;

    console.log("-----------------------------------------");
    console.log("[TRACING] 1. Incoming request body:", JSON.stringify(input));

    // Validate required fields
    if (input.amount === undefined || !input.remark) {
      return NextResponse.json(
        { error: "amount and remark are required" },
        { status: 400 }
      );
    }

    // Classify remark locally for UI presentation
    const remarkResult = classifyRemark(input.remark);
    
    // Construct exactly 22 features
    const features = buildFeatureVector(input);
    const flags = generateFlags(input);

    console.log("[TRACING] 2. Constructed 22-dimensional feature vector:", JSON.stringify(features));

    let fraudScore = 0.15;
    let riskLevel: RiskLevel = "low";
    let rawModelOutput = null;

    // Call Python FastAPI Model Server
    try {
      console.log(`[TRACING] 3. Calling FastAPI model at ${MODEL_API_URL}/predict with features...`);
      const response = await fetch(`${MODEL_API_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ features })
      });

      if (response.ok) {
        const prediction = await response.json();
        rawModelOutput = prediction;
        console.log("[TRACING] 4. Raw model output:", JSON.stringify(prediction));
        fraudScore = prediction.fraud_risk_score;
        riskLevel = prediction.risk_bucket.toLowerCase() as RiskLevel;
      } else {
        const errText = await response.text();
        console.error(`[TRACING] ERROR: Python API returned ${response.status}: ${errText}`);
      }
    } catch (err) {
      console.error(`[TRACING] ERROR: Python API fetch failed. Is the server running? URL: ${MODEL_API_URL}`, err);
    }

    const result: TransactionScore & { debug?: any } = {
      riskScore: Math.round(fraudScore * 100),
      riskLevel: riskLevel,
      remarkCategory: remarkResult.category,
      remarkConfidence: remarkResult.confidence,
      flags,
      timestamp: new Date().toISOString(),
      debug: {
        featureVector: features,
        modelOutput: rawModelOutput || "Failed to hit model",
      }
    };

    console.log("[TRACING] 5. Final response to UI:", JSON.stringify(result));
    console.log("-----------------------------------------");

    return NextResponse.json(result);
  } catch (err) {
    console.error("[score-transaction] error:", err);
    return NextResponse.json(
      { error: "Failed to score transaction" },
      { status: 500 }
    );
  }
}
