// ─────────────────────────────────────────────
// Keyword/rule-based remark classifier
// Reads dynamically from data/keyword_rules.json exported from Databricks
// ─────────────────────────────────────────────
import fs from "fs";
import path from "path";
import { MessageAnalysisResult, RiskLevel } from "@/types";

interface CategoryRule {
  category: string;
  keywords: string[];
  riskLevel: RiskLevel;
  advice: string;
}

let cachedRules: CategoryRule[] | null = null;

function loadRules(): CategoryRule[] {
  if (cachedRules) return cachedRules;
  try {
    const filePath = path.join(process.cwd(), "data", "keyword_rules.json");
    if (fs.existsSync(filePath)) {
      const data = JSON.parse(fs.readFileSync(filePath, "utf-8"));
      cachedRules = data.rules || [];
      return cachedRules!;
    }
  } catch (err) {
    console.error("[Classifier] Failed to load keyword rules locally:", err);
  }
  return [];
}

/**
 * Analyze a UPI remark or suspicious message against known scam patterns.
 * Returns the matching category, confidence, and actionable advice.
 */
export function classifyRemark(message: string): MessageAnalysisResult {
  const rules = loadRules();
  const lower = message.toLowerCase().trim();

  if (!lower) {
    return {
      category: "UNKNOWN",
      confidence: 0,
      riskLevel: "low",
      matchedKeywords: [],
      advice: "Please enter a message to analyze.",
    };
  }

  let bestMatch: { rule: CategoryRule; matchCount: number; matched: string[] } | null = null;

  for (const rule of rules) {
    const matched: string[] = [];
    for (const kw of rule.keywords) {
      if (lower.includes(kw)) {
        matched.push(kw);
      }
    }

    if (matched.length > 0) {
      if (!bestMatch || matched.length > bestMatch.matchCount) {
        bestMatch = { rule, matchCount: matched.length, matched };
      }
    }
  }

  if (!bestMatch) {
    return {
      category: "LEGITIMATE",
      confidence: 0.7,
      riskLevel: "low",
      matchedKeywords: [],
      advice:
        "This message does not match known scam patterns. It appears to be a normal transaction remark. Stay alert and verify if unsure.",
    };
  }

  // Confidence scales with how many keywords matched
  const maxPossibleMatches = Math.max(1, bestMatch.rule.keywords.length);
  const rawConfidence = bestMatch.matchCount / Math.min(maxPossibleMatches, 5);
  const confidence = Math.min(Math.max(rawConfidence, 0.5), 0.98);

  return {
    category: bestMatch.rule.category,
    confidence: Math.round(confidence * 100) / 100,
    riskLevel: bestMatch.rule.riskLevel,
    matchedKeywords: bestMatch.matched,
    advice: bestMatch.rule.advice,
  };
}
