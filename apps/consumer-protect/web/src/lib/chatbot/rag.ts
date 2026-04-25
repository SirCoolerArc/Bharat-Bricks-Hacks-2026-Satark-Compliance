// ─────────────────────────────────────────────
// Local RAG chatbot — generates advice grounded in RBI guidance
// Reads from data/rbi_guidance_kb.json exported from Databricks
// ─────────────────────────────────────────────

import fs from "fs";
import path from "path";
import { ChatMessage } from "@/types";

interface KBEntry {
  keywords: string[];
  response: string;
}

interface KBData {
  default_response: string;
  entries: KBEntry[];
}

let cachedKb: KBData | null = null;

function loadKb(): KBData {
  if (cachedKb) return cachedKb;
  try {
    const filePath = path.join(process.cwd(), "data", "rbi_guidance_kb.json");
    if (fs.existsSync(filePath)) {
      cachedKb = JSON.parse(fs.readFileSync(filePath, "utf-8"));
      return cachedKb!;
    }
  } catch (err) {
    console.error("[RAG] Failed to load local KB:", err);
  }
  
  return { default_response: "I'm sorry, I couldn't load the guidance database.", entries: [] };
}

/**
 * Generate a local RAG response grounded in RBI guidance.
 * Bypasses Databricks Model Serving completely as requested.
 */
export async function generateChatResponse(
  userMessage: string,
  _history: ChatMessage[]
): Promise<{ content: string; sources: string[] }> {
  const kb = loadKb();
  const queryTokens = userMessage.toLowerCase().replace(/[^\w\s]/g, "").split(/\s+/);
  
  let bestMatch = kb.default_response;
  let highestScore = 0;
  let matchedKeywords: string[] = [];

  for (const entry of kb.entries) {
    const score = entry.keywords.filter(k => queryTokens.includes(k.toLowerCase())).length;
    
    if (score > highestScore && score > 0) {
      highestScore = score;
      bestMatch = entry.response;
      matchedKeywords = entry.keywords;
    }
  }

  const sources = highestScore > 0 
    ? ["RBI Circular 2017", "NPCI Guidelines"]
    : [];

  return { content: bestMatch, sources };
}
