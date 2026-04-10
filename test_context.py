from src import OpenAIEmbedder, FixedSizeChunker, RecursiveChunker, Document, EmbeddingStore, KnowledgeBaseAgent
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=False)

def demo_llm(prompt: str) -> str:
    # Print prompt để kiểm tra context được inject
    print("PROMPT INJECTED:")
    print(prompt[:800])
    return "[DEMO] Answer based on context"

# Load 1 file
doc = Document(
    id="test",
    content=Path("data/raw_data/6_quy_chế_sử_dụng_sản_phẩm_xanh_bike.md").read_text(),
    metadata={"source": "bike"}
)

chunker = RecursiveChunker(chunk_size=5000)
chunks = chunker.chunk(doc.content)
chunk_docs = [Document(id=f"chunk_{i}", content=ch, metadata={"doc_id": doc.id}) for i, ch in enumerate(chunks)]

embedder = OpenAIEmbedder()
store = EmbeddingStore(collection_name="grounding_test", embedding_fn=embedder)
store.add_documents(chunk_docs)

agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)
answer = agent.answer("Tôi mang theo thùng hàng cồng kềnh, tài xế có quyền từ chối không?", top_k=3)
print("\nAGENT ANSWER:")
print(answer)