"""
5 Benchmark Queries từ tài liệu Xanh SM (1-10)
Được trích xuất trực tiếp từ documents + có metadata để filter

Yêu cầu:
- Queries phải đa dạng (cover các product khác nhau)
- Gold answers copy từ tài liệu (không paraphrase)
- Ít nhất 1 query cần metadata filtering để tìm được kết quả tốt
"""

BENCHMARK_QUERIES = [
    {
        "id": "Q1",
        "query": "Đối tác không được gửi những loại hàng hóa nào qua Xanh Express?",
        "gold_answer": """Kim loại quý (vàng, bạc, v.v… ở dạng thỏi, nén, tiền xu, v.v…), hàng nguy hiểm, súng, vũ khí, đạn dược, thiết bị kỹ thuật quân sự, thuốc lá, chất gây nghiện, động vật sống, tiền tệ Việt Nam, ngoại tệ.""",
        "metadata": {
            "product": "xanh_express",
            "category": "quy_lac","document_source": "7_quy_chế_sử_dụng_sản_phẩm_xanh_express.md",
            "section": "3.1.2"
        },
        "requires_metadata_filter": True,
        "filter_hint": "product=xanh_express (để filter ra quy tắc riêng của Xanh Express)"
    },
    {
        "id": "Q2",
        "query": "Nếu tài liệu bị mất trong quá trình gửi qua Xanh Express với Gói bảo hiểm Vàng, mức bồi thường tối đa là bao nhiêu?",
        "gold_answer": "1.000.000 VNĐ trên mỗi đơn hàng/điểm giao hàng (Áp dụng với Tài liệu)",
        "metadata": {
            "product": "xanh_express",
            "category": "bao_hiem",
            "document_source": "7_quy_chế_sử_dụng_sản_phẩm_xanh_express.md",
            "section": "4.3.2 (iv)"
        },
        "requires_metadata_filter": True,
        "filter_hint": "product=xanh_express"
    },
    {
        "id": "Q3",
        "query": "Người dùng hủy đơn hàng trên Xanh Ngon nhiều lần bằng phương thức Thanh toán khi nhận hàng sẽ bị xử lý như thế nào?",
        "gold_answer": "Tài khoản Người dùng có thể bị khóa. Ngoài ra, tài khoản của Người dùng có thể bị vô hiệu hóa phương thức 'Thanh toán khi nhận hàng' trong thời hạn nhất định.",
        "metadata": {
            "product": "xanh_ngon",
            "category": "huy_don",
            "document_source": "10_quy_chế_sử_dụng_sản_phẩm_xanh_ngon.md",
            "section": "6.1"
        },
        "requires_metadata_filter": True,
        "filter_hint": "product=xanh_ngon"
    },
    {
        "id": "Q4",
        "query": "Nếu Người dùng mang theo hành lý quá khổ trên Xanh Bike, Đối tác có quyền từ chối không?",
        "gold_answer": "Có. Đối tác có quyền từ chối cung cấp Sản Phẩm nếu Người dùng/Khách hàng mang theo đồ vật quá khổ mà Đối tác đánh giá là có khả năng vi phạm quy định pháp luật về giao thông đối với xe chở khách, không đảm bảo nguyên tắc an toàn.",
        "metadata": {
            "product": "xanh_bike",
            "category": "quy_dinh_hanh_ly",
            "document_source": "6_quy_chế_sử_dụng_sản_phẩm_xanh_bike.md",
            "section": "3.3"
        },
        "requires_metadata_filter": False
    },
    {
        "id": "Q5",
        "query": "Xanh SM có chịu trách nhiệm với các hàng hóa bị hư hỏng, thất lạc trong quá trình vận chuyển trên Xanh Ngon không?",
        "gold_answer": "Không. Xanh SM sẽ không chịu trách nhiệm đối với bất kỳ tổn thất, chi phí, phí tổn hoặc bất kỳ khoản phí nào phát sinh từ sự cố đó. Người dùng sẽ liên hệ với Đối tác vận chuyển hoặc Đối tác Thương nhân để giải quyết sự cố.",
        "metadata": {
            "product": "xanh_ngon",
            "category": "trach_nhiem",
            "document_source": "10_quy_chế_sử_dụng_sản_phẩm_xanh_ngon.md",
            "section": "5.2"
        },
        "requires_metadata_filter": False
    }
]


def print_benchmark_summary():
    """In bảng tóm tắt cho nhóm"""
    print("\n" + "="*100)
    print("📋 5 BENCHMARK QUERIES — XANH SM (Được trích từ 10 tài liệu)")
    print("="*100)

    for q in BENCHMARK_QUERIES:
        print(f"\n[{q['id']}] {q['query']}")
        print(f"    📄 Source: {q['metadata']['document_source']} (Mục {q['metadata']['section']})")
        print(f"    🏷️  Product: {q['metadata']['product']} | Category: {q['metadata']['category']}")
        if q['requires_metadata_filter']:
            print(f"    ⚠️  Cần filter metadata: {q['filter_hint']}")
        print(f"    ✅ Gold Answer: {q['gold_answer'][:100]}...")

    print("\n" + "="*100)
    print("📊 THỐNG KÊ:")
    print(f"   - Tổng queries: {len(BENCHMARK_QUERIES)}")
    print(f"   - Queries cần metadata filter: {sum(1 for q in BENCHMARK_QUERIES if q['requires_metadata_filter'])}")
    print(f"   - Products cover: {set(q['metadata']['product'] for q in BENCHMARK_QUERIES)}")
    print("="*100 + "\n")


if __name__ == "__main__":
    print_benchmark_summary()
