import os
import sys
from pathlib import Path
from src.models import Document
from src.chunking import FixedSizeChunker, SentenceChunker, RecursiveChunker
from src.store import EmbeddingStore
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from dotenv import load_dotenv

# Import the common group benchmark queries
try:
    from benchmark_queries_group import BENCHMARK_QUERIES
except ImportError:
    print("Error: benchmark_queries_group.py not found. Using empty list.")
    BENCHMARK_QUERIES = []

# Fix for Windows console encoding issues with Vietnamese characters
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# --- CONFIGURATION ---
DATA_DIR = Path("data/raw_data")

def get_embedder():
    """Select the embedder based on environment variables."""
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception as e:
            print(f"Failed to load LocalEmbedder: {e}. Falling back to mock.")
            return _mock_embed
    elif provider == "openai":
        try:
            return OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception as e:
            print(f"Failed to load OpenAIEmbedder: {e}. Falling back to mock.")
            return _mock_embed
    return _mock_embed

def load_documents():
    """Load all .md and .txt files from the data directory."""
    documents = []
    # Filter out common non-data files
    for file_path in DATA_DIR.glob("*"):
        if file_path.suffix in [".md", ".txt"] and file_path.name not in ["REPORT.md", "README.md", "REPORT_TEMPLATE.md"]:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Synchronize metadata keys with the group benchmark queries
                stem = file_path.stem.lower()
                product = "general"
                if "bike" in stem: product = "xanh_bike"
                elif "express" in stem: product = "xanh_express"
                elif "car" in stem: product = "xanh_car"
                elif "ngon" in stem: product = "xanh_ngon"
                elif "gia_đình" in stem: product = "xanh_family"
                
                doc = Document(
                    id=file_path.name,
                    content=content,
                    metadata={
                        "source": file_path.name,
                        "product": product
                    }
                )
                documents.append(doc)
    return documents

def run_benchmark_for_strategy(name, chunker, docs, queries):
    """Run all queries against a specific chunking strategy."""
    print(f"\n{'='*20} STRATEGY: {name} {'='*20}")
    
    # 1. Select Embedder
    embedder = get_embedder()
    print(f"-> Using Embedding Backend: {getattr(embedder, '_backend_name', embedder.__class__.__name__)}")

    # 1. Chunk and Index
    store = EmbeddingStore(collection_name=f"benchmark_{name.lower()}", embedding_fn=embedder)
    
    all_chunks = []
    for doc in docs:
        chunks = chunker.chunk(doc.content)
        for i, chunk_text in enumerate(chunks):
            chunk_doc = Document(
                id=f"{doc.id}_chunk_{i}",
                content=chunk_text,
                metadata={**doc.metadata, "chunk_index": i, "doc_id": doc.id}
            )
            all_chunks.append(chunk_doc)
    
    store.add_documents(all_chunks)
    print(f"-> Indexed {len(all_chunks)} chunks from {len(docs)} documents.")

    # 2. Run Queries
    print(f"\n{'Query':<40} | {'Std Score':<10} | {'Filt Score':<10} | {'Help?'}")
    print("-" * 80)

    for q in queries:
        question = q['query']
        product_filter = q['metadata'].get('product')
        
        # Standard search
        results_std = store.search(question, top_k=3)
        score_std = round(results_std[0].get('score', 0), 4) if results_std else 0
        
        # Filtered search
        score_filt = 0
        filter_help = "N/A"
        if q.get('requires_metadata_filter') or product_filter:
            results_filt = store.search_with_filter(question, top_k=3, metadata_filter={"product": product_filter})
            score_filt = round(results_filt[0].get('score', 0), 4) if results_filt else 0
            
            if score_filt > score_std:
                filter_help = "YES (+)"
            elif score_filt < score_std:
                filter_help = "NO (-)"
            else:
                filter_help = "SAME"
        
        print(f"{question[:40]:<40} | {score_std:<10} | {score_filt:<10} | {filter_help}")

def main():
    docs = load_documents()
    queries = BENCHMARK_QUERIES
    
    if not docs:
        print("No documents found in data/raw_data directory!")
        return
    if not queries:
        print("No queries found in benchmark_queries_group.py!")
        return

    # User's chosen strategy for individual comparison is Recursive
    strategies = [
        ("FixedSize", FixedSizeChunker(chunk_size=500, overlap=50)),
        ("Sentence", SentenceChunker(max_sentences_per_chunk=3)),
        ("Recursive", RecursiveChunker(chunk_size=500))
    ]

    for name, chunker in strategies:
        run_benchmark_for_strategy(name, chunker, docs, queries)

if __name__ == "__main__":
    main()
