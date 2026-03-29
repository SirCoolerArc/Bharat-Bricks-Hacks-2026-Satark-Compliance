"""
Layer 2B — RAG Agent
ChromaDB vector store with regulatory document chunks.
Retrieves top-k relevant chunks for REGULATORY and HYBRID queries.
"""

import os
import logging
from config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL, RAG_TOP_K

logger = logging.getLogger(__name__)

# Lazy-load heavy imports
_collection = None
_embed_fn = None


# ── Built-in regulatory chunks ────────────────────────────────────
# These serve as baseline context when PDFs aren't loaded yet.
BUILTIN_REGULATORY_CHUNKS = [
    {
        "id": "rbi_kyc_01",
        "text": (
            "Per RBI Master Direction on KYC (2016, updated 2024): All regulated entities must "
            "carry out Customer Due Diligence (CDD) at the time of account opening and periodically "
            "thereafter. For UPI-linked accounts, Video-KYC is acceptable. Banks must maintain "
            "records of all transactions for a minimum of 5 years after the business relationship "
            "has ended. Failure to comply attracts penalties under Section 13 of PMLA."
        ),
        "source": "RBI Master Direction KYC 2016/2024",
    },
    {
        "id": "rbi_kyc_02",
        "text": (
            "Per RBI Master Direction on KYC: Banks must implement a robust KYC process including "
            "risk categorisation of customers. High-risk customers include those from jurisdictions "
            "that do not adequately apply FATF recommendations. Simplified measures may be applied "
            "for low-risk customers with transaction limits of ₹10,000 per month and ₹1,00,000 per year."
        ),
        "source": "RBI Master Direction KYC 2016/2024",
    },
    {
        "id": "npci_upi_fraud_01",
        "text": (
            "Per NPCI UPI Circular on Fraud Reporting: Member banks must report all confirmed UPI "
            "fraud transactions to NPCI within 24 hours of detection. The report must include "
            "transaction reference ID, VPA details, fraud type classification, amount, and "
            "beneficiary bank details. Non-compliance will result in penalties up to ₹1 lakh per "
            "unreported incident."
        ),
        "source": "NPCI UPI Fraud Reporting Circular",
    },
    {
        "id": "npci_upi_fraud_02",
        "text": (
            "Per NPCI UPI Circular: Banks must implement real-time fraud detection systems for "
            "UPI transactions exceeding ₹5,000. Transactions flagged as high-risk must trigger "
            "a 2-factor authentication. Velocity checks must be implemented: more than 10 "
            "transactions in 1 hour from the same VPA should trigger an automatic hold and review."
        ),
        "source": "NPCI UPI Fraud Reporting Circular",
    },
    {
        "id": "rbi_circular_41_01",
        "text": (
            "Per RBI Circular RBI/2024-25/41 — Guidelines on UPI Fraud: Banks are directed to "
            "establish a dedicated UPI fraud monitoring cell with minimum 3 officers per shift. "
            "All HIGH risk alerts must be reviewed within 4 hours. The bank must file a Suspicious "
            "Transaction Report (STR) with FIU-IND within 7 days if fraud is confirmed. The "
            "bank's fraud monitoring system must achieve a minimum 85% detection rate for known "
            "fraud patterns."
        ),
        "source": "RBI/2024-25/41 UPI Fraud Guidelines",
    },
    {
        "id": "rbi_circular_41_02",
        "text": (
            "Per RBI Circular RBI/2024-25/41: Banks must maintain a fraud rate below 5% across "
            "all UPI transactions. States or regions exceeding 8% fraud rate for two consecutive "
            "quarters must trigger enhanced monitoring and a remediation plan submitted to RBI "
            "within 30 days. The prescribed penalty for non-compliance is ₹5 lakh per month of "
            "continued breach."
        ),
        "source": "RBI/2024-25/41 UPI Fraud Guidelines",
    },
    {
        "id": "npci_sla_01",
        "text": (
            "Per NPCI 90-Day SLA Rules for Complaint Resolution: All customer complaints related "
            "to UPI fraud must be resolved within 90 calendar days from the date of filing. "
            "Banking institutions must acknowledge receipt within 48 hours and provide a unique "
            "tracking reference. Resolution status must be updated on the bank's portal every 15 days."
        ),
        "source": "NPCI SLA Rules for Complaint Resolution",
    },
    {
        "id": "npci_sla_02",
        "text": (
            "Per NPCI SLA Rules: If a complaint is not resolved within 90 days, the bank must "
            "escalate to the Banking Ombudsman and compensate the customer at the rate of ₹100 "
            "per day of delay beyond 90 days, subject to a maximum of ₹5,000. Banks with more "
            "than 20% SLA breach rate will face enhanced audit and potential suspension from "
            "UPI dispute resolution framework."
        ),
        "source": "NPCI SLA Rules for Complaint Resolution",
    },
    {
        "id": "rbi_reporting_01",
        "text": (
            "Per RBI Framework on Digital Payment Fraud Reporting: Monthly fraud reports must be "
            "submitted by the 7th of each month covering all UPI/IMPS fraud incidents. Reports "
            "must break down fraud by type (phishing, social engineering, OTP interception, "
            "SIM swap), geography (state-wise), and amount band (Below ₹10K, ₹10K-1L, Above ₹1L). "
            "Quarterly trend analysis is mandatory."
        ),
        "source": "RBI Digital Payment Fraud Reporting Framework",
    },
    {
        "id": "rbi_reporting_02",
        "text": (
            "Per RBI Notification on Liability in UPI Fraud: In third-party fraud cases, the "
            "customer liability is zero if reported within 3 working days. For reporting between "
            "4-7 days, maximum liability is ₹10,000. Beyond 7 days, customer bears full liability. "
            "Banks must prominently display fraud reporting hotline numbers and provide 24x7 "
            "blocking facility for UPI IDs."
        ),
        "source": "RBI Liability Framework for UPI Fraud",
    },
]


def _get_embedding_function():
    """Lazy-load sentence-transformers embedding function."""
    global _embed_fn
    if _embed_fn is None:
        try:
            from chromadb.utils import embedding_functions
            _embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL
            )
        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}. Using default.")
            _embed_fn = None
    return _embed_fn


def _get_collection():
    """Lazy-load ChromaDB collection, seeding with built-in chunks if empty."""
    global _collection
    if _collection is not None:
        return _collection

    try:
        import chromadb

        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

        embed_fn = _get_embedding_function()
        kwargs = {"name": "satark_regulatory"}
        if embed_fn:
            kwargs["embedding_function"] = embed_fn

        _collection = client.get_or_create_collection(**kwargs)

        # Seed with built-in chunks if collection is empty
        if _collection.count() == 0:
            logger.info("Seeding ChromaDB with built-in regulatory chunks...")
            _collection.add(
                ids=[c["id"] for c in BUILTIN_REGULATORY_CHUNKS],
                documents=[c["text"] for c in BUILTIN_REGULATORY_CHUNKS],
                metadatas=[{"source": c["source"]} for c in BUILTIN_REGULATORY_CHUNKS],
            )
            logger.info(f"Seeded {len(BUILTIN_REGULATORY_CHUNKS)} regulatory chunks.")

    except Exception as e:
        logger.error(f"ChromaDB initialization failed: {e}")
        _collection = None

    return _collection


def retrieve_regulatory_context(query: str) -> tuple[str, list[dict]]:
    """
    Retrieve top-k relevant regulatory chunks from ChromaDB.
    Returns (full_text_context, list_of_metadata_sources).
    """
    collection = _get_collection()
    context_chunks = []
    metadata_sources = []

    if collection is not None:
        try:
            results = collection.query(
                query_texts=[query],
                n_results=RAG_TOP_K,
            )
            if results and results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    source_name = "Unknown"
                    if results["metadatas"] and results["metadatas"][0]:
                        source_name = results["metadatas"][0][i].get("source", "Unknown")
                    
                    dist = 0.0
                    if results["distances"] and results["distances"][0]:
                        dist = results["distances"][0][i]
                    
                    # Store as structured metadata for UI
                    metadata_sources.append({
                        "document_name": source_name,
                        "similarity_score": 1 - (dist / 2) if dist < 2 else 0, # Normalize for UI matching (assuming L2 dist)
                        "snippet": doc[:160] + "..." if len(doc) > 160 else doc,
                        "page_number": "N/A"
                    })
                    context_chunks.append(f"[Source: {source_name}]\n{doc}")
                
                return "\n\n---\n\n".join(context_chunks), metadata_sources

        except Exception as e:
            logger.warning(f"ChromaDB query failed: {e}. Falling back to keyword match.")

    # Fallback: simple keyword matching on built-in chunks
    return _keyword_fallback(query), []


def _keyword_fallback(query: str) -> str:
    """Simple keyword-based retrieval when ChromaDB is unavailable."""
    q = query.lower()
    scored = []
    for chunk in BUILTIN_REGULATORY_CHUNKS:
        words = chunk["text"].lower().split()
        score = sum(1 for word in q.split() if word in words)
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:RAG_TOP_K]

    chunks = []
    meta = []
    for _, chunk in top:
        chunks.append(f"[Source: {chunk['source']}]\n{chunk['text']}")
        meta.append({
            "document_name": chunk["source"],
            "similarity_score": 0.5, # Baseline for local fallback
            "snippet": chunk["text"][:160] + "...",
            "page_number": "N/A"
        })
    return "\n\n---\n\n".join(chunks), meta


def add_document_chunks(chunks: list[dict]) -> int:
    """
    Add new document chunks to the vector store.
    Each chunk should have: {id: str, text: str, source: str}
    Returns number of chunks added.
    """
    collection = _get_collection()
    if collection is None:
        raise RuntimeError("ChromaDB is not available")

    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[{"source": c.get("source", "uploaded")} for c in chunks],
    )
    return len(chunks)
