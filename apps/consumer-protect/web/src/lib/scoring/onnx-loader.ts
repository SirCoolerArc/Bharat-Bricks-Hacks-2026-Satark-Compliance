// ─────────────────────────────────────────────
// ONNX model loader for XGBoost fraud scorer
// Runs the local model_b_xgboost.onnx natively in Next.js backend
// ─────────────────────────────────────────────
import path from "path";
import fs from "fs";

let session: any | null = null;
let loadAttempted = false;

/**
 * Load the ONNX model (singleton). Returns the InferenceSession or null.
 */
async function getSession(): Promise<any | null> {
  if (loadAttempted) return session;
  loadAttempted = true;

  const modelPath = path.join(process.cwd(), "data", "model_b_xgboost.onnx");

  if (!fs.existsSync(modelPath)) {
    console.error("[onnx] Model file missing at:", modelPath);
    return null;
  }

  try {
    const ort = await import(/* webpackIgnore: true */ "onnxruntime-node");
    session = await ort.InferenceSession.create(modelPath);
    console.log("[onnx] Model successfully loaded into memory from", modelPath);
    return session;
  } catch (err) {
    console.error("[onnx] Failed to load onnxruntime-node. Ensure it is installed.", err);
    return null;
  }
}

/**
 * Run inference on a 7-feature vector using the exported XGBoost ONNX model.
 * Returns a fraud probability (0–1).
 */
export async function scoreFraud(features: number[]): Promise<number> {
  const sess = await getSession();

  if (sess) {
    try {
      const ort = await import(/* webpackIgnore: true */ "onnxruntime-node");
      const inputTensor = new ort.Tensor("float32", Float32Array.from(features), [1, features.length]);

      const inputName = sess.inputNames[0] || "float_input";
      const results = await sess.run({ [inputName]: inputTensor });

      const outputName = sess.outputNames[sess.outputNames.length - 1]; // usually probabilities
      const output = results[outputName];

      if (output?.data) {
        // Depending on sklearn converter, proba might be an array of P(Class=0), P(Class=1)
        const data = output.data as Float32Array;
        return data.length >= 2 ? data[1] : data[0];
      }
    } catch (err) {
      console.error("[onnx] Inference failed at runtime:", err);
    }
  }

  // Fallback if model fails to load/run (just for safety so UI doesn't crash)
  console.warn("Falling back to safe default score due to ONNX error.");
  return 0.15; 
}
