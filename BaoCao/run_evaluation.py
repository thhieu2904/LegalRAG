"""
Script đánh giá hệ thống LegalRAG - Luận văn Chương 4
=====================================================

Đánh giá ở 2 mức độ:
1. DOCUMENT-LEVEL: Hit Rate, MRR, Top-1 Accuracy
2. CHUNK-LEVEL: Precision@K, Recall@K, F1-Score (yêu cầu ground truth chunk IDs)

Chạy: python run_evaluation.py

Output:
- evaluation_results.json: Kết quả chi tiết
- final_report.md: Báo cáo Markdown (copy vào luận văn)
"""

import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
import statistics

# ============================================
# CONFIGURATION
# ============================================

def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_test_set():
    with open('test_set.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# ============================================
# API EVALUATION
# ============================================

def query_api(base_url: str, query: str, session_id: str = "eval_session") -> Dict:
    """Gọi API query-service"""
    try:
        start_time = time.time()
        response = requests.post(
            f"{base_url}/query",
            json={
                "question": query,
                "session_id": session_id
            },
            timeout=60
        )
        elapsed_ms = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            data['_elapsed_ms'] = elapsed_ms
            return data
        else:
            return {"error": f"HTTP {response.status_code}", "_elapsed_ms": elapsed_ms}
            
    except Exception as e:
        return {"error": str(e), "_elapsed_ms": 0}

# ============================================
# CHUNK-LEVEL METRICS (Precision, Recall, F1)
# ============================================

def calculate_precision_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int = 5) -> float:
    """
    Precision@K = (Số chunks đúng trong top K) / K
    """
    if not retrieved_ids or k <= 0:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_count = sum(1 for rid in top_k if rid in relevant_ids)
    return relevant_count / min(k, len(top_k))

def calculate_recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int = 5) -> float:
    """
    Recall@K = (Số chunks đúng tìm được trong top K) / (Tổng chunks đúng)
    """
    if not retrieved_ids or not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    found_count = sum(1 for rid in relevant_ids if rid in top_k)
    return found_count / len(relevant_ids)

def calculate_f1_score(precision: float, recall: float) -> float:
    """
    F1 = 2 × (Precision × Recall) / (Precision + Recall)
    """
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)

# ============================================
# DOCUMENT-LEVEL METRICS (Hit Rate, MRR, Top-1)
# ============================================

def get_hit_rate(retrieved_titles: List[str], expected_title: str) -> float:
    """Hit Rate: Có tìm thấy document mong đợi không?"""
    if not retrieved_titles or not expected_title:
        return 0.0
    expected_lower = expected_title.lower().strip()
    for title in retrieved_titles:
        if title and expected_lower in title.lower():
            return 1.0
    return 0.0

def get_mrr(retrieved_titles: List[str], expected_title: str) -> float:
    """MRR: 1/rank của document mong đợi"""
    if not retrieved_titles or not expected_title:
        return 0.0
    expected_lower = expected_title.lower().strip()
    for rank, title in enumerate(retrieved_titles, start=1):
        if title and expected_lower in title.lower():
            return 1.0 / rank
    return 0.0

def get_top1_accuracy(retrieved_titles: List[str], expected_title: str) -> float:
    """Top-1 Accuracy: Document đúng có ở vị trí 1 không?"""
    if not retrieved_titles or not expected_title:
        return 0.0
    expected_lower = expected_title.lower().strip()
    first_title = retrieved_titles[0] if retrieved_titles else ""
    if first_title and expected_lower in first_title.lower():
        return 1.0
    return 0.0

# ============================================
# MAIN EVALUATION
# ============================================

def run_evaluation():
    print("=" * 70)
    print("ĐÁNH GIÁ HỆ THỐNG LEGALRAG - LUẬN VĂN CHƯƠNG 4")
    print("=" * 70)
    print()
    
    # Load config and test set
    config = load_config()
    test_set = load_test_set()
    
    base_url = config['api_base_url']
    # Handle both array format and dict with 'queries' key
    queries = test_set if isinstance(test_set, list) else test_set.get('queries', [])
    
    print(f"📋 Test set: {len(queries)} câu hỏi")
    print(f"🔗 API URL: {base_url}")
    print()
    
    results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_queries": len(queries),
            "api_url": base_url
        },
        "per_query_results": [],
        "metrics": {}
    }
    
    # Metrics accumulators - Chunk level
    precisions = []
    recalls = []
    f1_scores = []
    
    # Metrics accumulators - Document level
    hit_rates = []
    mrrs = []
    top1_accuracies = []
    
    # Performance & quality
    latencies = []
    answer_rates = []
    clarification_count = 0
    
    # Timing breakdown accumulators
    timing_data = {'embed_ms': [], 'search_ms': [], 'rerank_ms': [], 'llm_ms': []}
    
    # Category breakdown
    category_results = {}
    
    for i, test_case in enumerate(queries):
        query_id = test_case['id']
        query_text = test_case['query']
        expected_doc = test_case.get('expected_document', '')
        relevant_chunks = set(test_case.get('relevant_chunk_ids', []))
        category = test_case.get('category', 'other')
        
        print(f"[{i+1}/{len(queries)}] {query_text[:60]}...")
        
        # Call API
        response = query_api(base_url, query_text, f"eval_{query_id}")
        
        if 'error' in response:
            print(f"   ❌ Error: {response['error']}")
            continue
        
        # Extract from API response
        retrieved_chunk_ids = []
        retrieved_titles = []
        
        if 'sources' in response:
            for src in response['sources']:
                chunk_id = src.get('chunk_id')
                if chunk_id:
                    retrieved_chunk_ids.append(chunk_id)
                title = src.get('document_title', '')
                if title:
                    retrieved_titles.append(title)
        
        # Calculate CHUNK-LEVEL metrics (only if we have ground truth)
        if relevant_chunks:
            precision = calculate_precision_at_k(retrieved_chunk_ids, relevant_chunks, k=5)
            recall = calculate_recall_at_k(retrieved_chunk_ids, relevant_chunks, k=5)
            f1 = calculate_f1_score(precision, recall)
        else:
            precision, recall, f1 = 0.0, 0.0, 0.0
        
        # Calculate DOCUMENT-LEVEL metrics
        hit = get_hit_rate(retrieved_titles, expected_doc)
        mrr = get_mrr(retrieved_titles, expected_doc)
        top1 = get_top1_accuracy(retrieved_titles, expected_doc)
        
        # Other metrics
        latency = response.get('_elapsed_ms', 0)
        has_answer = bool(response.get('answer')) and not response.get('needs_clarification')
        needs_clarif = response.get('needs_clarification', False)
        
        # Collect timing breakdown from API response
        timing = response.get('timing')
        if timing:
            for key in ['embed_ms', 'search_ms', 'rerank_ms', 'llm_ms']:
                if timing.get(key):
                    timing_data[key].append(timing[key])
        
        # Accumulate
        if relevant_chunks:  # Only add to chunk metrics if we have ground truth
            precisions.append(precision)
            recalls.append(recall)
            f1_scores.append(f1)
        
        hit_rates.append(hit)
        mrrs.append(mrr)
        top1_accuracies.append(top1)
        latencies.append(latency)
        answer_rates.append(1.0 if has_answer else 0.0)
        if needs_clarif:
            clarification_count += 1
        
        # Category breakdown
        if category not in category_results:
            category_results[category] = {'hits': 0, 'total': 0, 'latencies': []}
        category_results[category]['total'] += 1
        category_results[category]['hits'] += hit
        category_results[category]['latencies'].append(latency)
        
        # Store per-query result
        results['per_query_results'].append({
            "query_id": query_id,
            "query": query_text,
            "category": category,
            "expected_document": expected_doc,
            "relevant_chunk_count": len(relevant_chunks),
            "retrieved_chunk_ids": retrieved_chunk_ids[:5],
            "retrieved_documents": retrieved_titles[:3],
            # Chunk-level
            "precision@5": round(precision, 3),
            "recall@5": round(recall, 3),
            "f1_score": round(f1, 3),
            # Document-level
            "hit_rate": hit,
            "mrr": round(mrr, 3),
            "top1_accuracy": top1,
            # Quality
            "has_answer": has_answer,
            "needs_clarification": needs_clarif,
            "latency_ms": round(latency, 1),
            "answer_preview": response.get('answer', '')[:200] + "..." if response.get('answer') else ""
        })
        
        # Print summary
        status = "✅" if hit == 1.0 else "❌"
        clarif = " (clarif)" if needs_clarif else ""
        chunk_info = f"P={precision:.2f} R={recall:.2f} F1={f1:.2f}" if relevant_chunks else "no_ground_truth"
        print(f"   {status} {chunk_info} | Hit={hit:.0f} MRR={mrr:.2f} | {latency:.0f}ms{clarif}")
    
    # Aggregate metrics
    metrics = {}
    
    # Chunk-level (if available)
    if precisions:
        metrics["chunk_level"] = {
            "precision@5": {
                "mean": round(statistics.mean(precisions), 3),
                "std": round(statistics.stdev(precisions), 3) if len(precisions) > 1 else 0,
                "min": round(min(precisions), 3),
                "max": round(max(precisions), 3)
            },
            "recall@5": {
                "mean": round(statistics.mean(recalls), 3),
                "std": round(statistics.stdev(recalls), 3) if len(recalls) > 1 else 0,
                "min": round(min(recalls), 3),
                "max": round(max(recalls), 3)
            },
            "f1_score": {
                "mean": round(statistics.mean(f1_scores), 3),
                "std": round(statistics.stdev(f1_scores), 3) if len(f1_scores) > 1 else 0,
                "min": round(min(f1_scores), 3),
                "max": round(max(f1_scores), 3)
            },
            "queries_with_ground_truth": len(precisions)
        }
    
    # Document-level
    if hit_rates:
        metrics["document_level"] = {
            "hit_rate": {
                "mean": round(statistics.mean(hit_rates), 3),
                "count": int(sum(hit_rates)),
                "total": len(hit_rates),
                "percentage": round(statistics.mean(hit_rates) * 100, 1)
            },
            "mrr": {
                "mean": round(statistics.mean(mrrs), 3),
                "std": round(statistics.stdev(mrrs), 3) if len(mrrs) > 1 else 0
            },
            "top1_accuracy": {
                "mean": round(statistics.mean(top1_accuracies), 3),
                "count": int(sum(top1_accuracies)),
                "total": len(top1_accuracies),
                "percentage": round(statistics.mean(top1_accuracies) * 100, 1)
            }
        }
    
    # Answer quality
    metrics["answer_quality"] = {
        "answer_rate": {
            "mean": round(statistics.mean(answer_rates), 3),
            "count": int(sum(answer_rates)),
            "total": len(answer_rates),
            "percentage": round(statistics.mean(answer_rates) * 100, 1)
        },
        "clarification_rate": {
            "count": clarification_count,
            "total": len(queries),
            "percentage": round(clarification_count / len(queries) * 100, 1)
        }
    }
    
    # Performance
    if latencies:
        metrics["performance"] = {
            "latency_ms": {
                "mean": round(statistics.mean(latencies), 1),
                "std": round(statistics.stdev(latencies), 1) if len(latencies) > 1 else 0,
                "min": round(min(latencies), 1),
                "max": round(max(latencies), 1),
                "p95": round(sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0, 1)
            }
        }
        
        # Add timing breakdown
        if timing_data['embed_ms']:
            metrics['timing_breakdown'] = {
                'embed_ms': {
                    'mean': round(statistics.mean(timing_data['embed_ms']), 1),
                    'min': min(timing_data['embed_ms']),
                    'max': max(timing_data['embed_ms'])
                },
                'search_ms': {
                    'mean': round(statistics.mean(timing_data['search_ms']), 1),
                    'min': min(timing_data['search_ms']),
                    'max': max(timing_data['search_ms'])
                },
                'rerank_ms': {
                    'mean': round(statistics.mean(timing_data['rerank_ms']), 1),
                    'min': min(timing_data['rerank_ms']),
                    'max': max(timing_data['rerank_ms'])
                },
                'llm_ms': {
                    'mean': round(statistics.mean(timing_data['llm_ms']), 1),
                    'min': min(timing_data['llm_ms']),
                    'max': max(timing_data['llm_ms'])
                },
                'queries_with_timing': len(timing_data['embed_ms'])
            }
            # Calculate percentages
            total_mean = metrics['performance']['latency_ms']['mean']
            tb = metrics['timing_breakdown']
            sum_steps = tb['embed_ms']['mean'] + tb['search_ms']['mean'] + tb['rerank_ms']['mean'] + tb['llm_ms']['mean']
            tb['other_ms'] = {'mean': round(total_mean - sum_steps, 1)}
            for key in ['embed_ms', 'search_ms', 'rerank_ms', 'llm_ms', 'other_ms']:
                tb[key]['percentage'] = round(tb[key]['mean'] / total_mean * 100, 1) if total_mean > 0 else 0
    
    # Category breakdown
    metrics["by_category"] = {}
    for cat, data in category_results.items():
        metrics["by_category"][cat] = {
            "hit_rate": round(data['hits'] / data['total'], 3) if data['total'] > 0 else 0,
            "count": data['total'],
            "avg_latency_ms": round(statistics.mean(data['latencies']), 1) if data['latencies'] else 0
        }
    
    results['metrics'] = metrics
    
    # Save results
    with open('evaluation_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print()
    print("=" * 70)
    print("KẾT QUẢ TỔNG HỢP")
    print("=" * 70)
    
    if 'chunk_level' in metrics:
        m = metrics['chunk_level']
        print()
        print("📊 CHUNK-LEVEL METRICS (Retrieval Quality):")
        print(f"   Precision@5:  {m['precision@5']['mean']:.3f} ± {m['precision@5']['std']:.3f}")
        print(f"   Recall@5:     {m['recall@5']['mean']:.3f} ± {m['recall@5']['std']:.3f}")
        print(f"   F1-Score:     {m['f1_score']['mean']:.3f} ± {m['f1_score']['std']:.3f}")
        print(f"   (Based on {m['queries_with_ground_truth']} queries with ground truth)")
    
    if 'document_level' in metrics:
        m = metrics['document_level']
        print()
        print("📄 DOCUMENT-LEVEL METRICS:")
        print(f"   Hit Rate:     {m['hit_rate']['count']}/{m['hit_rate']['total']} ({m['hit_rate']['percentage']:.1f}%)")
        print(f"   MRR:          {m['mrr']['mean']:.3f}")
        print(f"   Top-1 Acc:    {m['top1_accuracy']['count']}/{m['top1_accuracy']['total']} ({m['top1_accuracy']['percentage']:.1f}%)")
    
    m = metrics['answer_quality']
    print()
    print("📝 ANSWER QUALITY:")
    print(f"   Answer Rate:        {m['answer_rate']['count']}/{m['answer_rate']['total']} ({m['answer_rate']['percentage']:.1f}%)")
    print(f"   Clarification Rate: {m['clarification_rate']['count']}/{m['clarification_rate']['total']} ({m['clarification_rate']['percentage']:.1f}%)")
    
    m = metrics['performance']
    print()
    print("⏱️  PERFORMANCE:")
    print(f"   Avg Latency:  {m['latency_ms']['mean']:.0f} ± {m['latency_ms']['std']:.0f} ms")
    print(f"   Min / Max:    {m['latency_ms']['min']:.0f} / {m['latency_ms']['max']:.0f} ms")
    print(f"   P95 Latency:  {m['latency_ms']['p95']:.0f} ms")
    
    print()
    print("📁 BY CATEGORY:")
    for cat, data in metrics['by_category'].items():
        print(f"   {cat}: Hit={data['hit_rate']:.1%} ({data['count']} queries) Lat={data['avg_latency_ms']:.0f}ms")
    
    # Timing breakdown
    if 'timing_breakdown' in metrics:
        tb = metrics['timing_breakdown']
        print()
        print("⏱️  TIMING BREAKDOWN (per step):")
        print(f"   Embedding:     {tb['embed_ms']['mean']:>6.0f} ms ({tb['embed_ms']['percentage']:.1f}%)")
        print(f"   Vector Search: {tb['search_ms']['mean']:>6.0f} ms ({tb['search_ms']['percentage']:.1f}%)")
        print(f"   Reranking:     {tb['rerank_ms']['mean']:>6.0f} ms ({tb['rerank_ms']['percentage']:.1f}%)")
        print(f"   LLM Generate:  {tb['llm_ms']['mean']:>6.0f} ms ({tb['llm_ms']['percentage']:.1f}%)")
        print(f"   Other:         {tb['other_ms']['mean']:>6.0f} ms ({tb['other_ms']['percentage']:.1f}%)")
        print(f"   (Based on {tb['queries_with_timing']} queries with timing data)")
    
    print()
    print("✅ Kết quả đã lưu: evaluation_results.json")
    
    # Generate report
    generate_report(results)
    
    return results

# ============================================
# REPORT GENERATION
# ============================================

def generate_report(results: Dict):
    """Tạo báo cáo chi tiết cho luận văn"""
    
    m = results.get('metrics', {})
    if not m:
        print("❌ Không có metrics để tạo báo cáo")
        return
    
    # Helper for target checking
    def check(val, target, op='>'):
        if op == '>':
            return '✅' if val > target else '❌'
        elif op == '>=':
            return '✅' if val >= target else '❌'
        elif op == '<':
            return '✅' if val < target else '❌'
        return '❓'
    
    report = f"""# KẾT QUẢ ĐÁNH GIÁ HỆ THỐNG LEGALRAG

> Báo cáo tự động - {results['metadata']['timestamp']}

## 1. Tổng quan đánh giá

| Thông số | Giá trị |
|----------|---------|
| Số câu hỏi test | {results['metadata']['total_queries']} |
| API endpoint | {results['metadata']['api_url']} |

---

## 2. Kết quả Retrieval - Mức Chunk

> Đánh giá khả năng tìm đúng **đoạn văn** liên quan (yêu cầu ground truth chunk IDs)

"""
    
    if 'chunk_level' in m:
        cl = m['chunk_level']
        report += f"""| Metric | Mean | Std | Min | Max | Mục tiêu | Đạt |
|--------|------|-----|-----|-----|----------|-----|
| **Precision@5** | {cl['precision@5']['mean']:.3f} | ±{cl['precision@5']['std']:.3f} | {cl['precision@5']['min']:.3f} | {cl['precision@5']['max']:.3f} | > 0.60 | {check(cl['precision@5']['mean'], 0.6)} |
| **Recall@5** | {cl['recall@5']['mean']:.3f} | ±{cl['recall@5']['std']:.3f} | {cl['recall@5']['min']:.3f} | {cl['recall@5']['max']:.3f} | > 0.60 | {check(cl['recall@5']['mean'], 0.6)} |
| **F1-Score** | {cl['f1_score']['mean']:.3f} | ±{cl['f1_score']['std']:.3f} | {cl['f1_score']['min']:.3f} | {cl['f1_score']['max']:.3f} | > 0.60 | {check(cl['f1_score']['mean'], 0.6)} |

*Số queries có ground truth: {cl['queries_with_ground_truth']}*

"""
    else:
        report += "*Không có ground truth chunk IDs trong test set*\n\n"
    
    # Document level
    report += """---

## 3. Kết quả Retrieval - Mức Document

> Đánh giá khả năng tìm đúng **văn bản** liên quan

"""
    
    if 'document_level' in m:
        dl = m['document_level']
        report += f"""| Metric | Giá trị | Chi tiết | Mục tiêu | Đạt |
|--------|---------|----------|----------|-----|
| **Hit Rate** | {dl['hit_rate']['percentage']:.1f}% | {dl['hit_rate']['count']}/{dl['hit_rate']['total']} | > 80% | {check(dl['hit_rate']['mean'], 0.8)} |
| **MRR** | {dl['mrr']['mean']:.3f} | ±{dl['mrr']['std']:.3f} | > 0.70 | {check(dl['mrr']['mean'], 0.7)} |
| **Top-1 Accuracy** | {dl['top1_accuracy']['percentage']:.1f}% | {dl['top1_accuracy']['count']}/{dl['top1_accuracy']['total']} | > 70% | {check(dl['top1_accuracy']['mean'], 0.7)} |

"""
    
    # Answer quality
    aq = m['answer_quality']
    report += f"""---

## 4. Chất lượng câu trả lời

| Metric | Giá trị | Chi tiết | Ghi chú |
|--------|---------|----------|---------|
| **Answer Rate** | {aq['answer_rate']['percentage']:.1f}% | {aq['answer_rate']['count']}/{aq['answer_rate']['total']} | Câu hỏi được trả lời trực tiếp |
| **Clarification Rate** | {aq['clarification_rate']['percentage']:.1f}% | {aq['clarification_rate']['count']}/{aq['clarification_rate']['total']} | Câu hỏi cần làm rõ |

"""
    
    # Performance
    perf = m['performance']
    report += f"""---

## 5. Hiệu năng hệ thống

| Metric | Giá trị | Mục tiêu | Đạt |
|--------|---------|----------|-----|
| **Thời gian phản hồi TB** | {perf['latency_ms']['mean']:.0f} ms | < 10,000 ms | {check(perf['latency_ms']['mean'], 10000, '<')} |
| **Độ lệch chuẩn** | ±{perf['latency_ms']['std']:.0f} ms | - | - |
| **Thời gian Min** | {perf['latency_ms']['min']:.0f} ms | - | - |
| **Thời gian Max** | {perf['latency_ms']['max']:.0f} ms | < 15,000 ms | {check(perf['latency_ms']['max'], 15000, '<')} |
| **P95 Latency** | {perf['latency_ms']['p95']:.0f} ms | - | - |

"""
    
    # Timing breakdown
    if 'timing_breakdown' in m:
        tb = m['timing_breakdown']
        report += f"""### 5.1. Phân tích thời gian từng bước

| Bước | Thời gian TB | Tỷ lệ |
|------|-------------|-------|
| Embedding query | {tb['embed_ms']['mean']:.0f} ms | {tb['embed_ms']['percentage']:.1f}% |
| Vector search | {tb['search_ms']['mean']:.0f} ms | {tb['search_ms']['percentage']:.1f}% |
| Reranking | {tb['rerank_ms']['mean']:.0f} ms | {tb['rerank_ms']['percentage']:.1f}% |
| LLM Generation | {tb['llm_ms']['mean']:.0f} ms | {tb['llm_ms']['percentage']:.1f}% |
| Other | {tb['other_ms']['mean']:.0f} ms | {tb['other_ms']['percentage']:.1f}% |
| **Tổng** | **{perf['latency_ms']['mean']:.0f} ms** | **100%** |

*Dữ liệu từ {tb['queries_with_timing']} queries có timing đầy đủ*

"""
    
    # By category
    report += """---

## 6. Phân tích theo danh mục

| Danh mục | Hit Rate | Số queries | Latency TB |
|----------|----------|------------|------------|
"""
    
    for cat, data in m['by_category'].items():
        report += f"| {cat} | {data['hit_rate']:.1%} | {data['count']} | {data['avg_latency_ms']:.0f} ms |\n"
    
    # Detailed results
    report += """
---

## 7. Chi tiết từng câu hỏi

| # | Danh mục | Câu hỏi | P@5 | R@5 | F1 | Hit | Lat | KQ |
|---|----------|---------|-----|-----|-----|-----|-----|-----|
"""
    
    for r in results['per_query_results']:
        hit_icon = "✅" if r['hit_rate'] == 1.0 else "❌"
        query_short = r['query'][:35] + "..." if len(r['query']) > 35 else r['query']
        status = "Clarif" if r.get('needs_clarification') else ("OK" if r.get('has_answer') else "Err")
        report += f"| {r['query_id']} | {r['category']} | {query_short} | {r['precision@5']:.2f} | {r['recall@5']:.2f} | {r['f1_score']:.2f} | {hit_icon} | {r['latency_ms']:.0f} | {status} |\n"
    
    # Nhận xét
    report += """
---

## 8. Nhận xét và đánh giá

"""
    
    # Auto-generate analysis
    if 'chunk_level' in m:
        f1_mean = m['chunk_level']['f1_score']['mean']
        if f1_mean >= 0.7:
            report += f"- **F1-Score cao** ({f1_mean:.3f}): Hệ thống retrieval hoạt động tốt, cân bằng giữa precision và recall.\n"
        elif f1_mean >= 0.5:
            report += f"- **F1-Score khá** ({f1_mean:.3f}): Retrieval chấp nhận được nhưng có thể cải thiện.\n"
        else:
            report += f"- **F1-Score thấp** ({f1_mean:.3f}): Cần cải thiện embedding hoặc chunking strategy.\n"
    
    if 'document_level' in m:
        hit = m['document_level']['hit_rate']['mean']
        if hit >= 0.8:
            report += f"- **Hit Rate cao** ({hit:.1%}): Hầu hết câu hỏi tìm đúng văn bản liên quan.\n"
        else:
            report += f"- **Hit Rate cần cải thiện** ({hit:.1%}): Một số câu hỏi không tìm được văn bản đúng.\n"
    
    lat = m['performance']['latency_ms']['mean']
    if lat < 5000:
        report += f"- **Thời gian phản hồi nhanh** ({lat:.0f}ms): Đáp ứng tốt yêu cầu < 10s.\n"
    elif lat < 10000:
        report += f"- **Thời gian phản hồi chấp nhận được** ({lat:.0f}ms): Trong ngưỡng cho phép.\n"
    else:
        report += f"- **Thời gian phản hồi chậm** ({lat:.0f}ms): Cần tối ưu LLM generation.\n"
    
    clarif = m['answer_quality']['clarification_rate']['percentage']
    if clarif > 0:
        report += f"- **Clarification Rate {clarif:.1f}%**: Hệ thống yêu cầu làm rõ khi câu hỏi mơ hồ - đây là tính năng thiết kế, không phải lỗi.\n"
    
    report += """
---
*Báo cáo được tạo tự động bởi LegalRAG Evaluation Script*
"""

    with open('final_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("✅ Báo cáo đã lưu: final_report.md")

# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":
    run_evaluation()
