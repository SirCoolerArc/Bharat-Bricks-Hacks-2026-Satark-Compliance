// ─────────────────────────────────────────────
// Databricks SQL Statement Execution API client
// Docs: https://docs.databricks.com/api/workspace/statementexecution
// ─────────────────────────────────────────────

interface StatementResponse {
  statement_id: string;
  status: { state: string; error?: { message: string } };
  manifest?: { schema: { columns: { name: string }[] } };
  result?: { data_array: string[][] };
}

const POLL_INTERVAL_MS = 500;
const MAX_POLLS = 60; // 30 seconds max wait

function getConfig() {
  const host = process.env.DATABRICKS_HOST;
  const token = process.env.DATABRICKS_TOKEN;
  const warehouseId = process.env.DATABRICKS_WAREHOUSE_ID;
  const catalog = process.env.DATABRICKS_CATALOG || "satark";
  const schema = process.env.DATABRICKS_SCHEMA || "gold";

  if (!host || !token || !warehouseId) {
    return null;
  }

  return { host: host.replace(/\/$/, ""), token, warehouseId, catalog, schema };
}

/** Returns true if Databricks credentials are configured */
export function isDatabricksConfigured(): boolean {
  return getConfig() !== null;
}

/**
 * Execute a SQL statement against the Databricks SQL Warehouse.
 * Returns an array of row objects keyed by column name.
 * Returns null if credentials are missing or the query fails.
 */
export async function executeStatement(
  sql: string
): Promise<Record<string, string>[] | null> {
  const config = getConfig();
  if (!config) {
    console.warn("[databricks] credentials not configured — returning null");
    return null;
  }

  try {
    // Submit statement
    const submitRes = await fetch(
      `${config.host}/api/2.0/sql/statements/`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${config.token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          warehouse_id: config.warehouseId,
          catalog: config.catalog,
          schema: config.schema,
          statement: sql,
          wait_timeout: "30s",
          disposition: "INLINE",
          format: "JSON_ARRAY",
        }),
      }
    );

    if (!submitRes.ok) {
      console.error("[databricks] submit failed:", submitRes.status, await submitRes.text());
      return null;
    }

    let data: StatementResponse = await submitRes.json();

    // Poll until terminal state
    let polls = 0;
    while (data.status.state === "PENDING" || data.status.state === "RUNNING") {
      if (polls++ >= MAX_POLLS) {
        console.error("[databricks] statement timed out");
        return null;
      }
      await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));

      const pollRes = await fetch(
        `${config.host}/api/2.0/sql/statements/${data.statement_id}`,
        {
          headers: { Authorization: `Bearer ${config.token}` },
        }
      );
      data = await pollRes.json();
    }

    if (data.status.state !== "SUCCEEDED") {
      console.error("[databricks] statement failed:", data.status.error?.message);
      return null;
    }

    // Map result rows to objects
    const columns = data.manifest?.schema.columns.map((c) => c.name) || [];
    const rows = data.result?.data_array || [];

    return rows.map((row) => {
      const obj: Record<string, string> = {};
      columns.forEach((col, i) => {
        obj[col] = row[i];
      });
      return obj;
    });
  } catch (err) {
    console.error("[databricks] unexpected error:", err);
    return null;
  }
}
