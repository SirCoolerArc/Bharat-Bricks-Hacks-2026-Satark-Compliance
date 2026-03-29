import os
import glob
import pypdf
import chromadb
from chromadb.utils import embedding_functions

try:
    import pandas as pd
except ImportError:
    pd = None


# Config
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DOCS_DIR = os.path.join(DATA_DIR, "rbi_docs")
CHROMA_DB_DIR = os.path.join(DATA_DIR, "chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE_WORDS = 500
CHUNK_OVERLAP_WORDS = 50

# Ensure directories exist
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(CHROMA_DB_DIR, exist_ok=True)

# Hardcoded regulatory facts (from User Prompt)
HARDCODED_DOCS = [
    {
        "source": "Document 1 — RBI UPI Fraud Reporting SLA",
        "text": "As per NPCI circular, banks are required to resolve UPI fraud complaints within 90 days. "
                "Complaints not resolved within 30 days must be escalated to the nodal officer. "
                "Banks failing SLA thresholds are subject to penalty under RBI Master Direction on Customer Service."
    },
    {
        "source": "Document 2 — RBI KYC Fraud Classification",
        "text": "KYC-based UPI frauds involve social engineering where victims are told their account will be "
                "blocked unless they complete KYC via a payment link. RBI Circular RBI/2024-25/41 specifically "
                "flags UPI remarks containing terms like 'KYC penalty', 'account block', 'urgent KYC' as "
                "high-confidence fraud indicators."
    },
    {
        "source": "Document 3 — NPCI Investment Fraud Advisory",
        "text": "Investment scams via UPI have shown 340% increase in 2024. Common patterns: UPI remarks "
                "mentioning 'return', 'processing fee', 'today only', 'investment profit'. NPCI advisory "
                "recommends real-time remark scanning as a fraud prevention measure."
    },
    {
        "source": "Document 4 — RBI Impersonation Fraud Circular",
        "text": "Impersonation frauds include CBI officer, IT department, electricity board, and telecom "
                "company impersonation. RBI Circular 2024 notes that impersonation fraud average transaction "
                "value is 3.2x higher than other fraud types. States with high government employee density "
                "show elevated impersonation fraud rates."
    },
    {
        "source": "Document 5 — SATARK Data Schema Reference",
        "text": "The SATARK system monitors 150,031 UPI transactions. Risk tiers: HIGH (recipient VPA age "
                "<14 days AND unique_senders_7d >50, OR new device AND IP mismatch, OR VPN AND short session). "
                "MEDIUM (any single device/IP/VPN flag). LOW (none). Gold tables: geo_heatmap (28 states), "
                "risk_distribution (tier × state × amount), scam_taxonomy (7 scam types), "
                "hourly_fraud_pattern (hour × day × state), alert_effectiveness (bank × status × scam)."
    },
    {
        "source": "Document 6 — RBI Harmonisation of TAT for Failed Transactions",
        "text": "Per RBI Framework (RBI/2019-20/67 DPSS.CO.PD No.629): For UPI transactions where the account "
                "is debited but transaction confirmation is not received at the merchant's location "
                "(payment to merchant), the bank is mandated to perform an auto-reversal within T + 5 days. "
                "If the delay exceeds T + 5 days, the bank must provide compensation of ₹100/- per day "
                "to the customer/merchant as applicable."
    }
]

# Initialize ChromaDB client and collection
client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)

# Use get_or_create to allow safely running this script multiple times
collection = client.get_or_create_collection(
    name="satark_regulatory",
    embedding_function=embed_fn,
    metadata={"description": "SATARK Regulatory Knowledge Base"}
)

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_WORDS, overlap: int = CHUNK_OVERLAP_WORDS) -> list[str]:
    """Chunks text into segments of approximate word counts with overlap."""
    words = text.split()
    chunks = []
    
    if not words:
        return chunks
        
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        
        if end == len(words):
            break
            
        start += (chunk_size - overlap)
        
    return chunks

def process_pdfs():
    """Reads all PDFs in rbi_docs, chunks them, and adds to ChromaDB."""
    pdf_files = glob.glob(os.path.join(DOCS_DIR, "*.pdf"))
    
    if not pdf_files:
        print(f"No PDFs found in {DOCS_DIR}. Skipping PDF ingestion.")
        return 0

    print(f"Found {len(pdf_files)} PDFs in {DOCS_DIR}.")
    
    total_chunks = 0
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        try:
            reader = pypdf.PdfReader(pdf_path)
            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + " "
            
            chunks = chunk_text(full_text, CHUNK_SIZE_WORDS, CHUNK_OVERLAP_WORDS)
            
            if chunks:
                ids = [f"{filename}_chunk_{i}" for i in range(len(chunks))]
                docs = chunks
                metadatas = [{"source": filename} for _ in range(len(chunks))]
                
                collection.add(
                    ids=ids,
                    documents=docs,
                    metadatas=metadatas
                )
                
                print(f"✓ Embedded {len(chunks)} chunks for '{filename}'")
                total_chunks += len(chunks)
            else:
                print(f"⚠ Skipping '{filename}' (no extractable text)")
                
        except Exception as e:
            print(f"❌ Error processing '{filename}': {e}")
            
    return total_chunks

def process_hardcoded_facts():
    """Embeds the 5 hardcoded synthetic documents provided in the prompt."""
    print("Processing hardcoded regulatory facts...")
    
    ids = []
    docs = []
    metadatas = []
    
    for i, doc in enumerate(HARDCODED_DOCS):
        # Even though these are short, process through the chunk function for consistency
        chunks = chunk_text(doc["text"], CHUNK_SIZE_WORDS, CHUNK_OVERLAP_WORDS)
        
        for j, chunk in enumerate(chunks):
            doc_id = f"hardcoded_doc_{i+1}_chunk_{j}"
            # Only add if it doesn't already exist to avoid duplicate errors on re-run
            existing = collection.get(ids=[doc_id])
            if existing and existing["ids"]:
                # If running multiple times, we can just update instead or skip
                pass 
                
            ids.append(doc_id)
            docs.append(chunk)
            metadatas.append({"source": doc["source"]})
            
            
    if docs:
        # upsert used instead of add to gracefully overwrite if the script is run multiple times
        collection.upsert(
            ids=ids,
            documents=docs,
            metadatas=metadatas
        )
        print(f"✓ Embedded {len(docs)} chunks across {len(HARDCODED_DOCS)} synthetic rules.")
        return len(docs)
    return 0

def process_csv_summaries():
    """Generates textual summaries of Silver and Gold CSV tables and embeds them in Chroma DB."""
    if pd is None:
        print("Pandas not installed. Skipping CSV summary generation.")
        return 0
        
    print("Processing CSV tables into RAG context...")
    docs = []
    
    # Gold Table: Geo Heatmap
    geo_path = os.path.join(DATA_DIR, "gold_tables", "geo_heatmap.csv")
    if os.path.exists(geo_path):
        df = pd.read_csv(geo_path)
        top_fraud = df.sort_values(by="fraud_rate_pct", ascending=False).head(5)
        text = "Gold Table: Geo Heatmap. Summarizes fraud by state. "
        text += "The top 5 states by fraud rate are: "
        for _, row in top_fraud.iterrows():
            text += f"{row['sender_state']} ({row['fraud_rate_pct']}% fraud rate, {row['fraud_txns']} fraud txns out of {row['total_txns']}). "
        docs.append({"source": "geo_heatmap.csv", "text": text})

    # Gold Table: Risk Distribution
    risk_path = os.path.join(DATA_DIR, "gold_tables", "risk_distribution.csv")
    if os.path.exists(risk_path):
        df = pd.read_csv(risk_path)
        text = "Gold Table: Risk Distribution. Shows transaction risk tiers. "
        for _, row in df.iterrows():
            text += f"{row['rule_risk_tier']} tier has {row['txn_count']} transactions with {row['fraud_rate_pct']}% fraud rate. "
        docs.append({"source": "risk_distribution.csv", "text": text})

    # Gold Table: Scam Taxonomy
    scam_path = os.path.join(DATA_DIR, "gold_tables", "scam_taxonomy.csv")
    if os.path.exists(scam_path):
        df = pd.read_csv(scam_path)
        text = "Gold Table: Scam Taxonomy. Breakdown of fraud types. "
        for _, row in df.iterrows():
            text += f"{row['scam_type']} has {row['complaint_count']} complaints and a total loss of {row['total_loss']} (units). "
        docs.append({"source": "scam_taxonomy.csv", "text": text})

    # Gold Table: Alert Effectiveness
    alert_path = os.path.join(DATA_DIR, "gold_tables", "alert_effectiveness.csv")
    if os.path.exists(alert_path):
        df = pd.read_csv(alert_path)
        text = "Gold Table: Alert Effectiveness. Performance per bank. "
        # Group by bank for a summary
        if 'bank_id' in df.columns and 'avg_resolution_days' in df.columns:
            bank_grouped = df.groupby('bank_id')['avg_resolution_days'].mean().sort_values().dropna()
            text += f"Top banks resolving complaints fast: "
            for bank, days in bank_grouped.head(3).items():
                text += f"{bank} ({days:.1f} avg days). "
        docs.append({"source": "alert_effectiveness.csv", "text": text})

    # Gold Table: Hourly Fraud
    hourly_path = os.path.join(DATA_DIR, "gold_tables", "hourly_fraud_pattern.csv")
    if os.path.exists(hourly_path):
        df = pd.read_csv(hourly_path)
        top_hour = df.sort_values(by="fraud_rate_pct", ascending=False).iloc[0]
        text = f"Gold Table: Hourly Fraud. The most risky hour is {top_hour['txn_hour']}:00 with a fraud rate of {top_hour['fraud_rate_pct']}%. "
        docs.append({"source": "hourly_fraud_pattern.csv", "text": text})

    # Silver Table: Complaints
    comp_path = os.path.join(DATA_DIR, "silver_tables", "complaints_enriched.csv")
    if os.path.exists(comp_path):
        df = pd.read_csv(comp_path)
        total_comp = len(df)
        resolved = len(df[df['status'] == 'RESOLVED']) if 'status' in df.columns else "unknown"
        text = f"Silver Table: Complaints Enriched. Contains {total_comp} total individual UPI fraud complaints. {resolved} of these have been RESOLVED."
        docs.append({"source": "complaints_enriched.csv", "text": text})
        
    # Silver Table: Transactions
    txn_path = os.path.join(DATA_DIR, "silver_tables", "transactions_enriched.csv")
    if os.path.exists(txn_path):
        try:
            total_txns = sum(1 for _ in open(txn_path, 'r')) - 1
            text = f"Silver Table: Transactions Enriched. A large dataset containing {total_txns} individual UPI transactions with device IP flags, amount, timestamp, and rule risk tier evaluations."
            docs.append({"source": "transactions_enriched.csv", "text": text})
        except Exception:
            pass

    # Embed these summary blocks into Chroma
    total_embedded = 0
    ids, documents, metadatas = [], [], []
    for i, item in enumerate(docs):
        chunks = chunk_text(item["text"], CHUNK_SIZE_WORDS, CHUNK_OVERLAP_WORDS)
        for j, chunk in enumerate(chunks):
            doc_id = f"csv_summary_{i}_chunk_{j}"
            existing = collection.get(ids=[doc_id])
            if not existing or not existing["ids"]:
                ids.append(doc_id)
                documents.append(chunk)
                metadatas.append({"source": item["source"]})
    
    if ids:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        total_embedded = len(ids)
                
    if total_embedded > 0:
        print(f"✓ Embedded {total_embedded} CSV summary chunks.")
    return total_embedded


def retrieve_context(query: str, n_results: int = 3) -> list[dict]:
    """
    Retrieve top-k relevant chunks from ChromaDB.
    Returns list of {text, source, relevance_score}
    """
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    output = []
    if results and results["documents"] and results["documents"][0]:
        docs = results["documents"][0]
        metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)
        # distances generally correlate to relevance_score (often lower distance is higher relevance depending on metric)
        distances = results["distances"][0] if results["distances"] else [0.0] * len(docs)
        
        for doc, meta, dist in zip(docs, metas, distances):
            output.append({
                "text": doc,
                "source": meta.get("source", "Unknown"),
                "relevance_score": dist  
            })
            
    return output

if __name__ == "__main__":
    print("========================================")
    print("SATARK RAG PIPELINE SETUP")
    print("========================================")
    
    # 1. Start vector DB parsing for PDFs
    pdf_chunks = process_pdfs()
    
    # 2. Add synthetic documents (the 5 hardcoded prompt items)
    hardcoded_chunks = process_hardcoded_facts()
    
    # 3. Add CSV data summaries
    csv_chunks = process_csv_summaries()
    
    print("----------------------------------------")
    print(f"Setup Complete. Total chunks now in DB: {collection.count()}")
    print("----------------------------------------")
    
    # 3. Quick Test using retrieve_context() as requested
    test_q = "What is the SLA for complaining about UPI fraud?"
    print(f"\nTEST QUERY: '{test_q}'")
    results = retrieve_context(test_q, n_results=2)
    
    for i, r in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f" -> Source: {r['source']}")
        print(f" -> Relevance Distance (lower is closer): {r['relevance_score']:.4f}")
        print(f" -> Text Snippet: {r['text'][:150]}...")
