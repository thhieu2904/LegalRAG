# HƯỚNG DẪN ĐÁNH GIÁ HỆ THỐNG LEGALRAG

## 📊 TỔNG QUAN

Hệ thống RAG cần đánh giá theo **3 khía cạnh chính**:
1. **Retrieval Quality**: Vector search có tìm đúng tài liệu không?
2. **Answer Quality**: Câu trả lời có chính xác và có nguồn gốc không?
3. **System Performance**: Hệ thống có nhanh và ổn định không?

---

## 1. RETRIEVAL METRICS (Đánh giá độ chính xác truy xuất)

### 1.1. Precision@K
**Định nghĩa:** Tỷ lệ tài liệu **relevant** trong top K kết quả trả về.

**Công thức:**
```
Precision@K = (Số tài liệu relevant trong top K) / K
```

**Ví dụ:**
- Query: "Thủ tục xin cấp giấy khai sinh"
- Top 5 chunks: [relevant, relevant, irrelevant, relevant, irrelevant]
- Precision@5 = 3/5 = 0.6 (60%)

**Cách đo:**
```python
def calculate_precision_at_k(retrieved_chunks, relevant_chunk_ids, k):
    top_k = retrieved_chunks[:k]
    relevant_count = sum(1 for chunk in top_k if chunk['id'] in relevant_chunk_ids)
    return relevant_count / k

# Ví dụ
retrieved = [
    {'id': 'chunk_1', 'score': 0.85},  # relevant
    {'id': 'chunk_2', 'score': 0.82},  # relevant
    {'id': 'chunk_3', 'score': 0.78},  # irrelevant
    {'id': 'chunk_4', 'score': 0.75},  # relevant
    {'id': 'chunk_5', 'score': 0.70},  # irrelevant
]
relevant_ids = {'chunk_1', 'chunk_2', 'chunk_4', 'chunk_7'}

precision_5 = calculate_precision_at_k(retrieved, relevant_ids, k=5)
print(f"Precision@5: {precision_5:.2f}")  # 0.60
```

**Target:** Precision@5 > 0.7 là tốt

---

### 1.2. Recall@K
**Định nghĩa:** Tỷ lệ tài liệu relevant được tìm thấy trong top K so với **tất cả** tài liệu relevant.

**Công thức:**
```
Recall@K = (Số relevant docs trong top K) / (Tổng số relevant docs)
```

**Ví dụ:**
- Tổng có 10 chunks relevant cho query
- Top 5 chứa 3 chunks relevant
- Recall@5 = 3/10 = 0.3 (30%)

**Code:**
```python
def calculate_recall_at_k(retrieved_chunks, relevant_chunk_ids, k):
    top_k = retrieved_chunks[:k]
    found_count = sum(1 for chunk in top_k if chunk['id'] in relevant_chunk_ids)
    total_relevant = len(relevant_chunk_ids)
    return found_count / total_relevant if total_relevant > 0 else 0

recall_5 = calculate_recall_at_k(retrieved, relevant_ids, k=5)
print(f"Recall@5: {recall_5:.2f}")  # 0.75 (3/4)
```

**Target:** Recall@10 > 0.8 là tốt

---

### 1.3. MRR (Mean Reciprocal Rank)
**Định nghĩa:** Vị trí trung bình của **chunk relevant đầu tiên**.

**Công thức:**
```
RR = 1 / (vị trí của chunk relevant đầu tiên)
MRR = trung bình RR của tất cả queries
```

**Ví dụ:**
- Query 1: Chunk relevant đầu tiên ở vị trí 2 → RR = 1/2 = 0.5
- Query 2: Chunk relevant đầu tiên ở vị trí 1 → RR = 1/1 = 1.0
- Query 3: Chunk relevant đầu tiên ở vị trí 5 → RR = 1/5 = 0.2
- **MRR = (0.5 + 1.0 + 0.2) / 3 = 0.57**

**Code:**
```python
def calculate_mrr(retrieved_chunks, relevant_chunk_ids):
    for rank, chunk in enumerate(retrieved_chunks, start=1):
        if chunk['id'] in relevant_chunk_ids:
            return 1.0 / rank
    return 0.0  # Không tìm thấy relevant chunk

# Tính MRR cho nhiều queries
def calculate_mean_mrr(queries_results):
    rr_scores = []
    for query_result in queries_results:
        rr = calculate_mrr(query_result['retrieved'], query_result['relevant_ids'])
        rr_scores.append(rr)
    return sum(rr_scores) / len(rr_scores)
```

**Target:** MRR > 0.7 là tốt

---

### 1.4. Hit Rate@K
**Định nghĩa:** Tỷ lệ queries có **ít nhất 1 chunk relevant** trong top K.

**Công thức:**
```
Hit Rate@K = (Số queries có ≥1 relevant trong top K) / (Tổng số queries)
```

**Code:**
```python
def calculate_hit_rate_at_k(queries_results, k):
    hits = 0
    for query_result in queries_results:
        top_k = query_result['retrieved'][:k]
        relevant_ids = query_result['relevant_ids']
        
        # Kiểm tra có ít nhất 1 relevant chunk không
        if any(chunk['id'] in relevant_ids for chunk in top_k):
            hits += 1
    
    return hits / len(queries_results)

# Ví dụ
queries = [
    {'retrieved': retrieved, 'relevant_ids': relevant_ids},
    # ... more queries
]
hit_rate = calculate_hit_rate_at_k(queries, k=5)
print(f"Hit Rate@5: {hit_rate:.2%}")
```

**Target:** Hit Rate@5 > 0.9 là tốt

---

### 1.5. NDCG@K (Normalized Discounted Cumulative Gain)
**Định nghĩa:** Đánh giá **thứ tự ranking**, documents relevant ở vị trí cao hơn được điểm tốt hơn.

**Công thức:**
```
DCG@K = Σ (relevance_score / log2(position + 1))
NDCG@K = DCG@K / IDCG@K  (IDCG = ideal DCG với ranking hoàn hảo)
```

**Code:**
```python
import math

def calculate_dcg_at_k(retrieved_chunks, relevance_scores, k):
    dcg = 0.0
    for i, chunk in enumerate(retrieved_chunks[:k]):
        relevance = relevance_scores.get(chunk['id'], 0)
        position = i + 1
        dcg += relevance / math.log2(position + 1)
    return dcg

def calculate_ndcg_at_k(retrieved_chunks, relevance_scores, k):
    # DCG thực tế
    dcg = calculate_dcg_at_k(retrieved_chunks, relevance_scores, k)
    
    # IDCG (ideal DCG): Sắp xếp theo relevance giảm dần
    sorted_scores = sorted(relevance_scores.values(), reverse=True)[:k]
    idcg = sum(score / math.log2(i + 2) for i, score in enumerate(sorted_scores))
    
    return dcg / idcg if idcg > 0 else 0.0

# Ví dụ: relevance score (0-3)
# 0 = không liên quan, 1 = hơi liên quan, 2 = liên quan, 3 = rất liên quan
relevance_scores = {
    'chunk_1': 3,  # rất liên quan
    'chunk_2': 2,  # liên quan
    'chunk_3': 0,  # không liên quan
    'chunk_4': 2,  # liên quan
    'chunk_5': 1,  # hơi liên quan
}

ndcg_5 = calculate_ndcg_at_k(retrieved, relevance_scores, k=5)
print(f"NDCG@5: {ndcg_5:.3f}")
```

**Target:** NDCG@5 > 0.8 là tốt

---

## 2. ANSWER QUALITY METRICS (Đánh giá chất lượng câu trả lời)

### 2.1. Correctness (Độ chính xác)
**Định nghĩa:** Câu trả lời có đúng về mặt thông tin không?

**Cách đo:** Manual evaluation bởi domain experts (luật sư, cán bộ tư pháp)

**Rating scale:**
- 0: Sai hoàn toàn
- 1: Một phần đúng nhưng thiếu thông tin quan trọng
- 2: Đúng nhưng không đầy đủ
- 3: Đúng và đầy đủ

**Process:**
```python
# Chuẩn bị test set
test_queries = [
    {
        'query': 'Thủ tục xin cấp giấy khai sinh',
        'ground_truth': 'Hồ sơ gồm: 1) Giấy chứng sinh...',
        'expected_citations': ['Điều 15 Luật Hộ tịch 2014']
    },
    # ... 50-100 queries
]

# Collect answers từ system
for test in test_queries:
    response = query_system(test['query'])
    test['system_answer'] = response['answer']
    test['citations'] = response['citations']

# Expert đánh giá
# Có thể dùng Google Form hoặc annotation tool
```

**Target:** Correctness score > 2.5/3.0

---

### 2.2. Faithfulness (Trung thực với context)
**Định nghĩa:** Câu trả lời có **grounded** trong chunks được retrieve không? Không hallucinate?

**Cách đo tự động với LLM-as-judge:**
```python
def evaluate_faithfulness(answer, retrieved_chunks):
    """
    Sử dụng LLM để kiểm tra answer có dựa vào chunks không
    """
    chunks_text = "\n\n".join([c['content'] for c in retrieved_chunks])
    
    prompt = f"""
Bạn là một expert đánh giá hệ thống RAG.

CONTEXT (các chunks được retrieve):
{chunks_text}

ANSWER (câu trả lời của hệ thống):
{answer}

TASK: Đánh giá xem ANSWER có được support hoàn toàn bởi CONTEXT không?

Trả lời theo format:
- Score: 0 (không grounded) / 1 (một phần grounded) / 2 (hoàn toàn grounded)
- Explanation: [Giải thích]

Score:"""

    # Call LLM (Gemini, GPT-4, etc.)
    response = llm_call(prompt)
    score = extract_score(response)  # Parse score từ response
    
    return score / 2.0  # Normalize to 0-1

# Ví dụ
answer = "Theo Điều 15, hồ sơ cấp giấy khai sinh gồm giấy chứng sinh..."
chunks = [
    {'content': 'Điều 15. Hồ sơ khai sinh\n1. Giấy chứng sinh...'},
    {'content': 'Điều 16. Thời hạn khai sinh...'}
]
faithfulness = evaluate_faithfulness(answer, chunks)
print(f"Faithfulness: {faithfulness:.2f}")
```

**Target:** Faithfulness > 0.9

---

### 2.3. Answer Relevancy (Độ liên quan)
**Định nghĩa:** Câu trả lời có trả lời đúng câu hỏi không?

**Cách đo:**
```python
def evaluate_answer_relevancy(query, answer):
    """
    Embed query và answer, tính cosine similarity
    Hoặc dùng LLM-as-judge
    """
    # Method 1: Embedding similarity
    query_emb = embed_text(query)
    answer_emb = embed_text(answer)
    similarity = cosine_similarity(query_emb, answer_emb)
    
    return similarity

# Method 2: LLM-as-judge (chính xác hơn)
def llm_judge_relevancy(query, answer):
    prompt = f"""
Query: {query}
Answer: {answer}

Câu trả lời có trả lời đúng câu hỏi không?
Score: 0 (không liên quan) / 1 (liên quan một phần) / 2 (hoàn toàn liên quan)
"""
    response = llm_call(prompt)
    return extract_score(response) / 2.0
```

**Target:** Relevancy > 0.85

---

### 2.4. Citation Accuracy
**Định nghĩa:** % câu trả lời có **citation chính xác** (Điều X, khoản Y).

**Cách đo:**
```python
def evaluate_citation_accuracy(answer, citations, ground_truth_citations):
    """
    Kiểm tra citations trong answer có match ground truth không
    """
    if not citations:
        return 0.0
    
    correct_citations = 0
    for citation in citations:
        # Normalize citation format
        normalized = normalize_citation(citation)
        if normalized in ground_truth_citations:
            correct_citations += 1
    
    return correct_citations / len(citations)

# Ví dụ
answer = "Theo Điều 15 khoản 1, hồ sơ gồm giấy chứng sinh..."
citations = ['Điều 15 Luật Hộ tịch 2014', 'Điều 16']
ground_truth = {'Điều 15 Luật Hộ tịch 2014'}

accuracy = evaluate_citation_accuracy(answer, citations, ground_truth)
```

**Target:** Citation accuracy > 0.9

---

## 3. PERFORMANCE METRICS (Hiệu năng hệ thống)

### 3.1. Latency (Response Time)
**Định nghĩa:** Thời gian từ khi nhận query đến khi trả về answer.

**Cách đo:** Đã có sẵn trong `query_logs.processing_time_ms`

**Breakdown:**
```python
def measure_latency_breakdown(query):
    """
    Đo latency từng bước trong pipeline
    """
    import time
    
    metrics = {}
    
    # 1. Embedding query
    start = time.time()
    query_embedding = embed_query(query)
    metrics['embedding_ms'] = (time.time() - start) * 1000
    
    # 2. Vector search
    start = time.time()
    candidates = vector_search(query_embedding, top_k=20)
    metrics['vector_search_ms'] = (time.time() - start) * 1000
    
    # 3. Reranking
    start = time.time()
    reranked = rerank_chunks(query, candidates, top_k=5)
    metrics['rerank_ms'] = (time.time() - start) * 1000
    
    # 4. LLM generation
    start = time.time()
    answer = generate_answer(query, reranked)
    metrics['generation_ms'] = (time.time() - start) * 1000
    
    metrics['total_ms'] = sum(metrics.values())
    
    return metrics

# Ví dụ output
{
    'embedding_ms': 150,
    'vector_search_ms': 80,
    'rerank_ms': 450,
    'generation_ms': 2800,
    'total_ms': 3480
}
```

**Targets:**
- Total latency: < 5000ms (5s)
- Embedding: < 200ms
- Vector search: < 100ms
- Reranking: < 500ms
- LLM generation: < 3000ms

---

### 3.2. Throughput (Queries per Second)
**Định nghĩa:** Số queries hệ thống xử lý được trong 1 giây.

**Cách đo:**
```python
import concurrent.futures
import time

def benchmark_throughput(queries, num_workers=10):
    """
    Gửi nhiều queries đồng thời để đo throughput
    """
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(query_system, q) for q in queries]
        results = [f.result() for f in futures]
    
    elapsed = time.time() - start_time
    qps = len(queries) / elapsed
    
    return {
        'total_queries': len(queries),
        'elapsed_seconds': elapsed,
        'queries_per_second': qps
    }

# Test với 100 queries
test_queries = ["Query 1", "Query 2", ...] * 100
metrics = benchmark_throughput(test_queries)
print(f"Throughput: {metrics['queries_per_second']:.2f} QPS")
```

**Target:** > 10 QPS (với single GPU)

---

### 3.3. Resource Usage
**Định nghĩa:** CPU, GPU, RAM usage.

**Cách đo:**
```python
import psutil
import subprocess

def measure_resource_usage():
    """
    Đo CPU, RAM, GPU usage
    """
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # RAM
    memory = psutil.virtual_memory()
    ram_used_gb = memory.used / (1024**3)
    ram_percent = memory.percent
    
    # GPU (NVIDIA)
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used', '--format=csv,noheader,nounits'],
            capture_output=True, text=True
        )
        gpu_util, gpu_mem = map(float, result.stdout.strip().split(','))
    except:
        gpu_util, gpu_mem = 0, 0
    
    return {
        'cpu_percent': cpu_percent,
        'ram_used_gb': ram_used_gb,
        'ram_percent': ram_percent,
        'gpu_utilization': gpu_util,
        'gpu_memory_mb': gpu_mem
    }

# Monitor trong quá trình chạy
import time
for i in range(10):
    metrics = measure_resource_usage()
    print(f"CPU: {metrics['cpu_percent']:.1f}% | RAM: {metrics['ram_percent']:.1f}% | GPU: {metrics['gpu_utilization']:.1f}%")
    time.sleep(5)
```

---

## 4. USER EXPERIENCE METRICS

### 4.1. User Satisfaction (Đánh giá người dùng)
**Cách đo:** Đã có sẵn trong `query_logs.user_rating` (1-5 stars)

**Analysis:**
```sql
-- Average rating
SELECT AVG(user_rating) as avg_rating
FROM query_logs
WHERE user_rating IS NOT NULL;

-- Rating distribution
SELECT user_rating, COUNT(*) as count
FROM query_logs
WHERE user_rating IS NOT NULL
GROUP BY user_rating
ORDER BY user_rating DESC;
```

**Target:** Average rating > 4.0/5.0

---

### 4.2. Task Completion Rate
**Định nghĩa:** % users hoàn thành được task (tìm được thông tin cần thiết).

**Cách đo:** User study với tasks cụ thể
```
Task 1: Tìm thủ tục xin cấp giấy khai sinh
Task 2: Tìm hồ sơ đăng ký bảo hiểm xã hội
...

Success = User tìm được đủ thông tin trong 3 phút
```

**Target:** > 85% completion rate

---

### 4.3. Query Reformulation Rate
**Định nghĩa:** % queries user phải hỏi lại (vì câu trả lời không rõ).

**Cách đo:** Analyze session history
```python
def calculate_reformulation_rate(sessions):
    """
    Đếm số lần user hỏi lại câu hỏi tương tự
    """
    reformulations = 0
    total_queries = 0
    
    for session in sessions:
        queries = session['queries']
        total_queries += len(queries)
        
        for i in range(1, len(queries)):
            # Check similarity với query trước đó
            similarity = compute_similarity(queries[i], queries[i-1])
            if similarity > 0.7:  # Queries tương tự
                reformulations += 1
    
    return reformulations / total_queries if total_queries > 0 else 0
```

**Target:** < 20% reformulation rate

---

## 5. CÁCH THU THẬP DỮ LIỆU ĐÁNH GIÁ

### Bước 1: Tạo Test Set (Ground Truth)

**Cần chuẩn bị:**
```python
# test_set.json
{
    "queries": [
        {
            "id": 1,
            "query": "Thủ tục xin cấp giấy khai sinh",
            "collection": "Hộ tịch",
            "relevant_chunk_ids": [
                "chunk_uuid_1",
                "chunk_uuid_2",
                "chunk_uuid_3"
            ],
            "ground_truth_answer": "Hồ sơ gồm: 1) Giấy chứng sinh...",
            "ground_truth_citations": [
                "Điều 15 Luật Hộ tịch 2014"
            ]
        },
        {
            "id": 2,
            "query": "Điều kiện đăng ký bảo hiểm xã hội",
            "collection": "Bảo hiểm",
            "relevant_chunk_ids": ["chunk_uuid_4", "chunk_uuid_5"],
            ...
        }
        // 50-100 queries tổng
    ]
}
```

**Làm sao tạo:**
1. Brainstorm queries thực tế users sẽ hỏi
2. Manually search trong PostgreSQL để tìm relevant chunks
3. Viết ground truth answer (hoặc copy từ văn bản gốc)
4. Note citations

---

### Bước 2: Run Evaluation Script

```python
# scripts/evaluate_system.py
import json
import numpy as np
from typing import List, Dict

def load_test_set(path='test_set.json'):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def query_system(query, collection=None):
    """
    Gọi API của query-service
    """
    import requests
    response = requests.post('http://localhost:8002/query', json={
        'query': query,
        'collection_slug': collection,
        'session_id': 'eval_session'
    })
    return response.json()

def evaluate_all_metrics(test_set):
    """
    Chạy evaluation toàn bộ
    """
    results = {
        'retrieval': {
            'precision@5': [],
            'recall@5': [],
            'mrr': [],
            'hit_rate@5': []
        },
        'answer': {
            'faithfulness': [],
            'relevancy': [],
            'citation_accuracy': []
        },
        'performance': {
            'latency_ms': []
        }
    }
    
    for test_case in test_set['queries']:
        print(f"Evaluating query {test_case['id']}: {test_case['query']}")
        
        # Query system
        response = query_system(test_case['query'], test_case['collection'])
        
        # 1. Retrieval metrics
        retrieved_ids = [c['id'] for c in response['chunks']]
        relevant_ids = set(test_case['relevant_chunk_ids'])
        
        precision = calculate_precision_at_k(retrieved_ids, relevant_ids, k=5)
        recall = calculate_recall_at_k(retrieved_ids, relevant_ids, k=5)
        mrr = calculate_mrr_single(retrieved_ids, relevant_ids)
        hit = 1.0 if any(id in relevant_ids for id in retrieved_ids[:5]) else 0.0
        
        results['retrieval']['precision@5'].append(precision)
        results['retrieval']['recall@5'].append(recall)
        results['retrieval']['mrr'].append(mrr)
        results['retrieval']['hit_rate@5'].append(hit)
        
        # 2. Answer metrics
        # (Implement faithfulness, relevancy evaluation)
        
        # 3. Performance
        results['performance']['latency_ms'].append(response['processing_time_ms'])
    
    # Aggregate results
    report = {
        'retrieval': {
            'precision@5': np.mean(results['retrieval']['precision@5']),
            'recall@5': np.mean(results['retrieval']['recall@5']),
            'mrr': np.mean(results['retrieval']['mrr']),
            'hit_rate@5': np.mean(results['retrieval']['hit_rate@5'])
        },
        'performance': {
            'avg_latency_ms': np.mean(results['performance']['latency_ms']),
            'p95_latency_ms': np.percentile(results['performance']['latency_ms'], 95)
        }
    }
    
    return report

# Run evaluation
if __name__ == '__main__':
    test_set = load_test_set()
    report = evaluate_all_metrics(test_set)
    
    # Print report
    print("\n" + "="*60)
    print("EVALUATION REPORT")
    print("="*60)
    
    print("\nRETRIEVAL METRICS:")
    print(f"  Precision@5: {report['retrieval']['precision@5']:.3f}")
    print(f"  Recall@5:    {report['retrieval']['recall@5']:.3f}")
    print(f"  MRR:         {report['retrieval']['mrr']:.3f}")
    print(f"  Hit Rate@5:  {report['retrieval']['hit_rate@5']:.3f}")
    
    print("\nPERFORMANCE:")
    print(f"  Avg Latency: {report['performance']['avg_latency_ms']:.0f} ms")
    print(f"  P95 Latency: {report['performance']['p95_latency_ms']:.0f} ms")
    
    # Save to file
    with open('evaluation_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
```

---

### Bước 3: Visualize Results

```python
# scripts/visualize_results.py
import matplotlib.pyplot as plt
import json

def plot_results(report_path='evaluation_report.json'):
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    # Plot retrieval metrics
    metrics = report['retrieval']
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Bar chart
    ax1 = axes[0]
    names = list(metrics.keys())
    values = list(metrics.values())
    ax1.bar(names, values, color=['#3498db', '#2ecc71', '#e74c3c', '#f39c12'])
    ax1.set_ylim(0, 1.0)
    ax1.set_title('Retrieval Metrics')
    ax1.set_ylabel('Score')
    
    # Latency histogram
    ax2 = axes[1]
    latencies = report['performance']['latency_ms']  # Nếu có raw data
    ax2.hist(latencies, bins=20, color='#9b59b6', edgecolor='black')
    ax2.set_title('Query Latency Distribution')
    ax2.set_xlabel('Latency (ms)')
    ax2.set_ylabel('Frequency')
    
    plt.tight_layout()
    plt.savefig('evaluation_results.png', dpi=300)
    print("Saved plot to evaluation_results.png")

if __name__ == '__main__':
    plot_results()
```

---

## 6. CHECKLIST ĐÁNH GIÁ CHO LUẬN VĂN

### ✅ Minimum (Cơ bản - BẮT BUỘC)
- [ ] **Precision@5**: Đo accuracy của vector search
- [ ] **MRR**: Đo vị trí chunk relevant đầu tiên
- [ ] **Average Latency**: Đo response time
- [ ] **User Rating**: Collect từ `query_logs.user_rating`

### ⭐ Good (Tốt - NÊN CÓ)
- [ ] **Recall@5**: Đo coverage của retrieval
- [ ] **Hit Rate@5**: % queries tìm được relevant docs
- [ ] **P95 Latency**: Latency worst-case
- [ ] **Faithfulness**: LLM-as-judge đánh giá hallucination
- [ ] **Citation Accuracy**: % answers có citation đúng

### 🚀 Excellent (Xuất sắc - LÝ TƯỞNG)
- [ ] **NDCG@5**: Đánh giá ranking quality
- [ ] **Answer Relevancy**: LLM judge relevancy
- [ ] **Throughput (QPS)**: Load testing
- [ ] **Resource Usage**: CPU/GPU/RAM monitoring
- [ ] **User Study**: 10-20 users test system, task completion rate
- [ ] **Comparison**: So sánh với baseline (keyword search, LLM thuần)

---

## 7. SAMPLE OUTPUT CHO LUẬN VĂN

### Bảng kết quả mẫu:

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Retrieval** | | | |
| Precision@5 | 0.82 | > 0.7 | ✅ |
| Recall@5 | 0.76 | > 0.7 | ✅ |
| MRR | 0.74 | > 0.7 | ✅ |
| Hit Rate@5 | 0.94 | > 0.9 | ✅ |
| NDCG@5 | 0.85 | > 0.8 | ✅ |
| **Answer Quality** | | | |
| Faithfulness | 0.92 | > 0.9 | ✅ |
| Relevancy | 0.88 | > 0.85 | ✅ |
| Citation Accuracy | 0.95 | > 0.9 | ✅ |
| Correctness (manual) | 2.7/3.0 | > 2.5 | ✅ |
| **Performance** | | | |
| Avg Latency | 3,200 ms | < 5,000 ms | ✅ |
| P95 Latency | 4,800 ms | < 6,000 ms | ✅ |
| Throughput | 12 QPS | > 10 QPS | ✅ |
| **User Experience** | | | |
| User Rating | 4.3/5.0 | > 4.0 | ✅ |
| Task Completion | 88% | > 85% | ✅ |

---

## 8. TOOLS HỖ TRỢ

### RAGAS (RAG Assessment)
```bash
pip install ragas
```

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)

from datasets import Dataset

# Chuẩn bị data
data = {
    'question': ['Query 1', 'Query 2', ...],
    'answer': ['Answer 1', 'Answer 2', ...],
    'contexts': [['Context 1', 'Context 2'], ...],
    'ground_truth': ['Ground truth 1', ...]
}
dataset = Dataset.from_dict(data)

# Evaluate
result = evaluate(
    dataset,
    metrics=[
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall
    ]
)

print(result)
```

---

## TÓM TẮT

**3 bước chính:**

1. **Tạo Test Set** (50-100 queries với ground truth)
2. **Run Evaluation Script** (đo các metrics tự động)
3. **Manual Review** (expert đánh giá correctness, user study)

**Metrics ưu tiên cao nhất cho luận văn:**
- Precision@5
- MRR
- Average Latency
- User Rating
- Faithfulness

Với hệ thống của bạn, dữ liệu đã có sẵn trong `query_logs` để phân tích latency và user rating. Phần còn lại cần tạo test set và chạy evaluation script!
