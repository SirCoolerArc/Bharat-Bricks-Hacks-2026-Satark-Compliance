import { NextRequest, NextResponse } from "next/server";
import { readFileSync, existsSync } from "fs";
import path from "path";

// 1. Data Types
interface KnowledgeChunk {
  text: string;
  category: string;
  keywords: string[];
  source: string;
}

interface FraudStats {
  fraud_rate: number;
  top_scam_type: string;
  recent_pattern: string;
  high_risk_states: string[];
}

// 2. Load Local Data
function loadData() {
  const kbPath = path.join(process.cwd(), "data", "knowledge_base.json");
  const statsPath = path.join(process.cwd(), "data", "fraud_stats.json");

  let kb: KnowledgeChunk[] = [];
  let stats: FraudStats | null = null;

  if (existsSync(kbPath)) {
    kb = JSON.parse(readFileSync(kbPath, "utf-8"));
  } else {
    // Fallback if the user hasn't explicitly placed these in the data folder
    console.warn("[RAG] knowledge_base.json not found at", kbPath);
  }

  if (existsSync(statsPath)) {
    stats = JSON.parse(readFileSync(statsPath, "utf-8"));
  }

  return { kb, stats };
}

// 3. Retrieval Logic
function retrieveChunks(question: string, kb: KnowledgeChunk[]): KnowledgeChunk[] {
  const qTerms = question.toLowerCase().split(/\W+/);

  // Score chunks based on keyword matching
  const scored = kb.map((chunk) => {
    let score = 0;
    chunk.keywords.forEach((kw) => {
      // Basic match
      if (question.toLowerCase().includes(kw.toLowerCase())) {
        score += 2;
      }
      // Token overlap
      if (qTerms.includes(kw.toLowerCase())) {
        score += 1;
      }
    });
    return { chunk, score };
  });

  // Sort descending by score
  scored.sort((a, b) => b.score - a.score);

  // Filter out chunks with 0 score (unless it's a very generic fallback)
  const matches = scored.filter((x) => x.score > 0).slice(0, 3);

  if (matches.length > 0) {
    return matches.map((m) => m.chunk);
  }

  // Fallback if no keywords matched: return "General Safety" and "Reporting" chunks
  return kb.filter(c => c.category === "General Safety" || c.category === "Reporting").slice(0, 2);
}

// 4. Build Context
function buildContext(chunks: KnowledgeChunk[], stats: FraudStats | null): string {
  let context = "[RBI GUIDANCE]\n";
  chunks.forEach((c) => {
    context += `- ${c.text} (Source: ${c.source})\n`;
  });

  if (stats) {
    context += `\n[CURRENT FRAUD LANDSCAPE]\n`;
    context += `Fraud rate: ${stats.fraud_rate}%\n`;
    context += `Top scam: ${stats.top_scam_type}\n`;
    context += `Recent pattern: ${stats.recent_pattern}\n`;
    context += `High risk regions: ${stats.high_risk_states.join(", ")}\n`;
  }

  return context;
}

// 5. API Route Implementation
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    // The UI currently passes { message, history }, but we must ensure we handle { question } too
    // based on strict prompt constraints.
    const userQuestion = body.question || body.message;

    if (!userQuestion || typeof userQuestion !== "string") {
      return NextResponse.json({ error: "question or message is required" }, { status: 400 });
    }

    // A. Load and Retrieve
    const { kb, stats } = loadData();
    const topChunks = retrieveChunks(userQuestion, kb);
    const contextString = buildContext(topChunks, stats);

    // B. Construct Gemini prompt
    const systemInstruction = `You are SATARK, an expert UPI fraud prevention and Indian financial safety assistant.

You are equipped with vast knowledge about banking, the RBI, UPI, and digital safety. Provide detailed, educational, and reassuring explanations to the user's questions.

CRITICAL RULES:
* If the user mentions being scammed, losing money, or asks for help with a fraud incident, you MUST instruct them to call the National Cyber Crime Helpline at 1930 immediately and report to cybercrime.gov.in.
* Integrate the provided [RBI GUIDANCE] into your answer if relevant.
* Be conversational, well-formatted, and empathetic. Use bullet points for readability.`;

    const geminiPayload = {
      systemInstruction: {
        parts: [{ text: systemInstruction }]
      },
      contents: [
        {
          role: "user",
          parts: [
            { text: `Context:\n${contextString}\n\nUser Question: ${userQuestion}` }
          ]
        }
      ],
      generationConfig: {
        temperature: 0.1, // Low temp for factual RAG
      }
    };

    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      console.warn("GEMINI_API_KEY is missing. Returning fallback.");
      return getFallbackResponse();
    }

    // C. Call Gemini using native fetch
    const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`;
    
    const tokenStart = Date.now();
    const gRes = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(geminiPayload),
    });

    if (!gRes.ok) {
      const errText = await gRes.text();
      console.error("[Gemini RAG] API Error:", gRes.status, errText);
      return getFallbackResponse();
    }

    const gData = await gRes.json();
    const answerText = gData.candidates?.[0]?.content?.parts?.[0]?.text || "Sorry, I couldn't generate a response.";

    // Ensure we comply with the requested `answer` shape, while passing `content` & `role` for UI compatibility
    return NextResponse.json({
      answer: answerText,
      content: answerText,
      role: "assistant",
      id: `msg-${Date.now()}`,
      timestamp: new Date().toISOString(),
      sources: topChunks.map((c) => c.source)
    });

  } catch (err) {
    console.error("[api/chat] error:", err);
    return getFallbackResponse();
  }
}

function getFallbackResponse() {
  return NextResponse.json({
    answer: "Please call 1930 immediately if this is urgent fraud.",
    content: "Please call 1930 immediately if this is urgent fraud.",
    role: "assistant",
    id: `msg-${Date.now()}`,
    timestamp: new Date().toISOString()
  });
}
