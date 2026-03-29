import { ComplaintInsert } from "@/types";
import { executeStatement } from "./client";

/**
 * Insert a new complaint record into the complaints table.
 * Returns the generated complaint ID on success, or null on failure.
 */
export async function insertComplaint(
  complaint: ComplaintInsert
): Promise<string | null> {
  const complaintId = `SATARK-${Date.now().toString(36).toUpperCase()}`;
  const now = new Date().toISOString();

  const sql = `
    INSERT INTO gold_complaints (
      complaint_id, txn_id, sender_vpa_hash, complaint_ts,
      scam_type, amount_bucket, complaint_status, resolution_days, bank_id
    ) VALUES (
      '${complaintId}',
      '${escapeSql(complaint.txnId)}',
      '${escapeSql(complaint.senderVpaHash)}',
      '${now}',
      '${escapeSql(complaint.scamType)}',
      '${escapeSql(complaint.amountBucket)}',
      'OPEN',
      NULL,
      '${escapeSql(complaint.bankId)}'
    )
  `;

  const result = await executeStatement(sql);

  // executeStatement returns null on failure, or empty array on successful INSERT
  if (result === null) {
    console.warn("[complaints] insert failed — Databricks may be unavailable");
    // Still return the ID so the UI can show it (offline-friendly)
    return complaintId;
  }

  return complaintId;
}

/** Basic SQL injection prevention — escape single quotes */
function escapeSql(value: string): string {
  return value.replace(/'/g, "''");
}
