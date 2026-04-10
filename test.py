import json
from pathlib import Path
from dotenv import load_dotenv

from src import (
    Document,
    EmbeddingStore,
    OpenAIEmbedder,
    FixedSizeChunker,
    SentenceChunker,
    RecursiveChunker,
)

load_dotenv()

data_dir = Path("data/raw_data")
testcase_path = Path("testcase/testcase.json")

# Load all md/txt in data/
files = sorted([p for p in data_dir.iterdir() if p.suffix.lower() in {".md", ".txt"} and p.name != ".gitkeep"])
print(f"Loaded file list ({len(files)} files):")
for p in files:
    print(" -", p)

raw_docs = []
for p in files:
    raw_docs.append(
        Document(
            id=p.stem,
            content=p.read_text(encoding="utf-8"),
            metadata={"source": str(p), "doc_id": p.stem}
        )
    )

testcases = json.loads(testcase_path.read_text(encoding="utf-8"))

strategies = {
    "fixed_size": FixedSizeChunker(chunk_size=700, overlap=80),
    "by_sentences": SentenceChunker(max_sentences_per_chunk=4),
    "recursive": RecursiveChunker(chunk_size=700),
}

embedder = OpenAIEmbedder()

for strategy_name, chunker in strategies.items():
    print("\n" + "="*80)
    print("STRATEGY:", strategy_name)

    chunk_docs = []
    for doc in raw_docs:
        chunks = chunker.chunk(doc.content)
        for i, ch in enumerate(chunks):
            chunk_docs.append(
                Document(
                    id=f"{doc.id}_chunk_{i}",
                    content=ch,
                    metadata={
                        "doc_id": doc.id,
                        "source": doc.metadata["source"],
                        "chunk_index": i,
                        "strategy": strategy_name,
                    },
                )
            )

    store = EmbeddingStore(collection_name=f"phase2_{strategy_name}", embedding_fn=embedder)
    store.add_documents(chunk_docs)

    print("Total chunks indexed:", store.get_collection_size())

    hit_top3 = 0
    for tc in testcases:
        q = tc["question"]
        expected = tc["expected_answer"].strip().lower()
        results = store.search(q, top_k=3)

        top_text = " ".join([r["content"] for r in results]).lower()
        hit = expected[:40] in top_text  # heuristic nhẹ để ước lượng hit
        hit_top3 += int(hit)

        top1 = results[0] if results else {"score": 0.0, "metadata": {}, "content": ""}
        print("\n-", tc["id"])
        print("  Q:", q)
        print("  Top1 score:", round(top1["score"], 4))
        print("  Top1 source:", top1["metadata"].get("source"))
        print("  Top1 preview:", top1["content"].replace("\n", " "), "...")
        print("  Hit@3 (heuristic):", hit)

    print(f"\nSummary {strategy_name}: hit_top3={hit_top3}/{len(testcases)}")
