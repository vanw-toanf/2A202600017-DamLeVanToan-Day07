# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Đàm Lê Văn Toàn - 2A202600017

**Nhóm:** A1

**Ngày:** 10/4

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Cosine similarity đo lường mức độ tương đồng về hướng giữa hai vector trong không gian đa chiều. Trong văn bản, giá trị cao (gần 1) nghĩa là hai đoạn văn có ngữ nghĩa hoặc chủ đề rất giống nhau, ngay cả khi chúng sử dụng các từ ngữ khác nhau.

**Ví dụ HIGH similarity:**
- Sentence A: "Làm thế nào để học lập trình Python hiệu quả?"
- Sentence B: "Cách tốt nhất để thành thạo ngôn ngữ Python là gì?"
- Tại sao tương đồng: Cả hai câu đều có cùng ý nghĩa là hỏi về phương pháp học tập ngôn ngữ lập trình Python.

**Ví dụ LOW similarity:**
- Sentence A: "Hôm nay trời nắng đẹp."
- Sentence B: "Cơ sở dữ liệu vector hoạt động như thế nào?"
- Tại sao khác: Một câu nói về thời tiết, câu còn lại nói về kiến thức kỹ thuật, không có sự liên quan về ngữ nghĩa.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Vì cosine similarity tập trung vào hướng của vector thay vì độ dài. Trong văn bản, một tài liệu dài và một tài liệu ngắn có cùng chủ đề sẽ có hướng vector tương tự nhau nhưng khoảng cách Euclidean sẽ rất lớn do sự khác biệt về số lượng từ.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* num_chunks = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11)
> *Đáp án:* 23 chunks

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Khi overlap tăng, số lượng chunk sẽ tăng lên vì mỗi chunk "mới" chỉ tiến thêm một khoảng ngắn hơn. Ta muốn overlap nhiều hơn để đảm bảo ngữ cảnh không bị cắt đứt đột ngột ở giữa các đoạn, giúp mô hình tìm kiếm dễ dàng tìm thấy các thông tin nằm ở ranh giới giữa hai chunk.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Quy chế và Điều khoản dịch vụ của Xanh SM (Grab-like service in Vietnam).

**Tại sao nhóm chọn domain này?**
> Nhóm chọn domain Xanh SM vì đây là bộ tài liệu thực tế, có cấu trúc phân mục rõ ràng và chứa nhiều thông tin chi tiết về chính sách, bồi thường, bảo mật. Việc xây dựng RAG trên bộ dữ liệu tiếng Việt này giúp giải quyết các bài toán hỗ trợ khách hàng thực tế và kiểm chứng khả năng hiểu ngữ nghĩa của tiếng Việt trong embedding.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | 1_điều_khoản_sử_dụng.md | Xanh SM | 42,252 | source, category_guess |
| 2 | 2_chính_sách_sử_dụng_cookies.md | Xanh SM | 7,242 | source, category_guess |
| 3 | 3_chính_sách_bảo_vệ_dữ_liệu_cá_nhân.md | Xanh SM | 35,162 | source, category_guess |
| 4 | 4_miễn_trừ_trách_nhiệm.md | Xanh SM | 1,341 | source, category_guess |
| 5 | 5_quy_trình_dành_cho_người_dùng.md | Xanh SM | 5,217 | source, category_guess |
| 6 | 6_quy_chế_sử_dụng_sản_phẩm_xanh_bike.md | Xanh SM | 3,323 | source, category_guess |
| 7 | 7_quy_chế_sử_dụng_sản_phẩm_xanh_express.md | Xanh SM | 14,804 | source, category_guess |
| 8 | 8_quy_chế_sử_dụng_sản_phẩm_xanh_car.md | Xanh SM | 3,349 | source, category_guess |
| 9 | 9_quy_chế_sử_dụng_tài_khoản_gia_đình.md | Xanh SM | 5,280 | source, category_guess |
| 10 | 10_quy_chế_sử_dụng_sản_phẩm_xanh_ngon.md | Xanh SM | 10,539 | source, category_guess |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| `source` | `str` | `1_điều_khoản_sử_dụng.md` | Giúp người dùng biết thông tin trích dẫn từ file nào. |
| `category_guess` | `str` | `Bike`, `Express`, `Car` | Cho phép lọc nhanh (filter) theo từng loại dịch vụ cụ thể để tăng độ chính xác. |

---

## 3. Chunking Strategy (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| Toàn bộ 10 docs | FixedSizeChunker (`fixed_size`) | 218 | ~500 | No (Cắt ngang câu, mất ngữ cảnh biên) |
| Toàn bộ 10 docs | SentenceChunker (`by_sentences`) | 239 | ~Varies | Yes (Theo câu, nhưng chunk có thể quá ngắn) |
| Toàn bộ 10 docs | RecursiveChunker (`recursive`) | 262 | ~500 | Yes (Giữ cấu trúc đoạn/mục, tối ưu cho RAG) |

**Phân tích (Chunk Coherence):**
Chiến lược `Recursive` tạo ra nhiều chunk nhất (262) nhưng đảm bảo tính mạch lạc cao nhất. So với `FixedSize`, nó không chỉ đảm bảo độ dài trung bình ổn định mà còn tôn trọng ranh giới ngữ nghĩa (\n\n, \n), giúp tránh việc thông tin quan trọng bị chia làm hai nửa.

### Strategy Của Tôi

**Loại:** FixedSizeChunker (`fixedsize`)

**Mô tả cách hoạt động:**
> `FixedSizedChunker` chia văn bản thành các đoạn có độ dài cố định theo ký tự (`chunk_size`). Mỗi chunk mới bắt đầu sau một bước `step = chunk_size - overlap`, nên nếu có `overlap` thì phần cuối chunk trước sẽ lặp lại ở đầu chunk sau để giữ ngữ cảnh liên tục. Nếu văn bản ngắn hơn `chunk_size` thì trả về đúng 1 chunk duy nhất.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Tôi chọn `FixedSizeChunker` làm chiến lược của mình vì đây là phương pháp cơ bản và đơn giản nhất. Việc sử dụng nó làm baseline giúp nhóm có một điểm so sánh rõ ràng để đánh giá hiệu quả của các chiến lược phức tạp hơn như `SentenceChunker` hay `RecursiveChunker`."

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| Toàn bộ 10 docs | SentenceChunker | 239 | ~Varies | Good (Nhưng đôi khi chunk quá ngắn) |
| Toàn bộ 10 docs | **FixedSizeChunker** (của tôi)** | 218 | ~500 | Ổn, không bị tình trạng chunk quá dài hoặc quá ngắn |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi <br> (2A202600017 <br> 2A202600075) | FixedSize | 7.1 | Đơn giản, tốc độ nhanh. | Hay bị "gãy" thông tin ở ranh giới chunk. |
| Teamate <br> (2A202600271 <br> 2A202600341)  | Recursive | 7.6 | Giữ ngữ cảnh phân cấp rất tốt. | Tốn nhiều chunk hơn. |
| Teammate <br> (2A202600342)| RecursiveChunker(300) + filter | 5 | Giữ cấu trúc đoạn, loại noise hiệu quả | Chunk vẫn có thể ngắn, mock embeddings hạn chế precision |
| Teammate <br>(2A202600271) | Sentence | 7.4 | Cấu trúc câu sạch sẽ. | Mất liên kết giữa các câu trong cùng đoạn. |


**Strategy nào tốt nhất cho domain này? Tại sao?**
> `RecursiveChunker` là tốt nhất cho domain quy chế/pháp lý vì nó bảo toàn tốt nhất cấu trúc nguyên bản của văn bản, giúp các thông tin đi kèm (như điều kiện loại trừ, mức bồi thường) không bị tách rời nhau.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Sử dụng regex `re.split(r'(?<=[.!?])\s+', text.strip())` để tách văn bản thành các câu dựa trên dấu chấm, hỏi, cảm thán. Sau đó, gom các câu này lại thành từng nhóm dựa trên tham số `max_sentences_per_chunk`.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Sử dụng danh sách các ký tự phân tách ưu tiên (như \n\n, \n, khoảng trắng). Nếu một đoạn văn bản sau khi tách vẫn dài hơn `chunk_size`, hàm sẽ đệ quy với ký tự phân tách tiếp theo cho đến khi đạt kích thước mong muốn hoặc hết ký tự phân tách.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Hỗ trợ lưu trữ cả ChromaDB (sử dụng `collection.add`) và In-memory (dùng danh sách Python). Tìm kiếm dựa trên việc tính toán độ tương đồng giữa embedding của truy vấn và tất cả các chunk đã lưu trữ.

**`search_with_filter` + `delete_document`** — approach:
> Lọc các bản ghi dựa trên metadata trước khi thực hiện tìm kiếm tương đồng. Xóa tài liệu bằng cách lọc bỏ tất cả các chunk có `doc_id` tương ứng trong metadata.

### KnowledgeBaseAgent

**`answer`** — approach:
> Triển khai luồng RAG: Tìm kiếm Top-K đoạn văn bản liên quan nhất, sau đó chèn chúng vào một template prompt làm ngữ cảnh (Context) rồi gửi cho LLM để sinh câu trả lời.

### Test Results

```
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
...
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED
============================= 42 passed in 0.19s ==============================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Python is a programming language. | Python is a programming language. | high | 1.0000 | Yes |
| 2 | Python is a programming language. | Java is also a coding language. | high | 0.8250 | Yes |
| 3 | I love eating apples. | The stock market is crashing. | low | 0.0150 | Yes |
| 4 | How do I fix my computer? | My PC is broken, help! | high | 0.7920 | Yes |
| 5 | The cat sat on the mat. | A feline was resting on the rug. | high | 0.8840 | Yes |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Kết quả bất ngờ nhất là các câu không dùng chung từ ngữ nhưng cùng ý nghĩa (Pair 5) vẫn có độ tương đồng rất cao. Điều này chứng tỏ embedding biểu diễn ngữ nghĩa (semantics) chứ không chỉ đơn thuần là so khớp từ ngữ (keyword matching).

---

## 6. Results (10 điểm)

### 6.1. Chi tiết kết quả (Retrieval Precision & Grounding)

Sử dụng thang điểm (Barem chuẩn):
- **2 điểm:** Top-3 có relevant chunk + Agent answer chính xác.
- **1 điểm:** Top-3 có relevant chunk nhưng answer thiếu chi tiết.
- **0 điểm:** Không retrieve được chunk relevant.

| # | Query (Tóm tắt) | Top-1 Source | Similarity | Relevant? | Precision (0-2) | Grounding |
|---|----------------|--------------|------------|-----------|-----------------|-----------|
| 1 | Xanh Express - Hàng cấm | 7_quy_chế...express.md | 0.7353 | Yes | 2 | Yes (Mục 3.1.2) |
| 2 | Bảo hiểm Vàng - Bồi thường | 7_quy_chế...express.md | 0.7334 | Yes | 2 | Yes (Mục 4.3.2) |
| 3 | Hủy đơn Xanh Ngon - Khóa TK | 10_quy_chế...ngon.md | 0.8757 | Yes | 2 | Yes (Mục 6.1) |
| 4 | Xanh Bike - Hành lý quá khổ | 6_quy_chế...bike.md | 0.7159 | Yes | 2 | Yes (Mục 3.3) |
| 5 | Xanh Ngon - Miễn trừ trách nhiệm | 10_quy_chế...ngon.md | 0.7914 | Yes | 2 | Yes (Mục 5.2) |

**Tổng điểm Retrieval Precision:** 10 / 10 (Đã đạt độ chính xác tuyệt đối với bộ câu hỏi chuẩn của nhóm).

### 6.2. Metadata Utility (Standard vs Filtered)

Dựa trên file `benchmark_queries_group.py` của nhóm:

| Query | Std Score | Filt Score | Help? |
|-------|-----------|------------|-------|
| 1. Xanh Express | 0.7353 | 0.7353 | SAME |
| 2. Bảo hiểm Vàng | 0.7334 | 0.7334 | SAME |
| 3. Hủy đơn | 0.8757 | 0.8757 | SAME |
| 4. Hành lý quá khổ | 0.7159 | 0.7159 | SAME |
| 5. Trách nhiệm | 0.7914 | 0.7914 | SAME |
**Nhận xét:** Với cấu trúc 10 tài liệu hiện tại, việc lọc theo `product` (xanh_bike, xanh_express...) cho kết quả tương đương với tìm kiếm toàn cục. Điều này cho thấy Embedding model đã phân loại ngữ nghĩa rất tốt, tự động đưa các tài liệu đúng service lên đầu mà không cần filter hỗ trợ.

### 6.3. Failure Analysis (Phân tích lỗi)

Mặc dù độ chính xác trên 5 câu benchmark của nhóm là 100%, tôi vẫn tìm thấy một trường hợp lỗi tiềm ẩn khi thử nghiệm các câu hỏi ngoài lề (Edge Cases):
- **Trường hợp:** Khi hỏi về "Tài khoản Gia đình đặt đồ ăn", hệ thống đôi khi vẫn bị nhầm lẫn sang "Xanh Bike" ở các model embedding yếu.
- **Giải thích:** Do các tài liệu quy chế có mẫu câu tương đồng. Giải pháp là cần metadata filtering mạnh hơn hoặc chuyển sang dùng model embedding chuyên dụng cho tiếng Việt.

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Tôi nhận thấy rằng việc sử dụng `SentenceChunker` có thể rất hiệu quả cho các FAQ ngắn, nhưng với các văn bản dài và phức tạp, Recursive vẫn là lựa chọn an toàn nhất để tránh mất thông tin ở biên.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Việc áp dụng Filter Metadata cần rất cẩn trọng. Nếu schema metadata quá hẹp, nó sẽ trở thành "con dao hai lưỡi" làm mất đi các thông tin quan trọng nằm ở các tài liệu bổ trợ hoặc điều khoản chung.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ cải thiện Metadata Utility bằng cách không chỉ lọc theo Category của query mà còn luôn luôn bao gồm (include) các file "Terms" chung của hệ thống vào kết quả tìm kiếm để tránh mất ngữ cảnh.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 4 / 5 |
| Document selection | Nhóm | 8 / 10 |
| Chunking strategy | Nhóm | 12 / 15 |
| My approach | Cá nhân | 8 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 8 / 10 |
| Core implementation (tests) | Cá nhân | 26 / 30 |
| Demo | Nhóm | 3 / 5 |
| **Tổng** | | **74 / 90** |
