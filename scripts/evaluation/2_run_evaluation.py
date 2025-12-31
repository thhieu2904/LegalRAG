"""
SCRIPT 2: RUN EVALUATION
Chạy evaluation tự động bằng cách gọi API của hệ thống

CÁCH DÙNG:
    python 2_run_evaluation.py

OUTPUT:
    - evaluation_results.json: Kết quả chi tiết
    - evaluation_summary.txt: Tóm tắt metrics
"""

import json
import time
import requests
from typing import Dict, List
from tqdm import tqdm
import numpy as np

from utils import (
    load_config,
    load_test_set,
    calculate_precision_at_k,
    calculate_recall_at_k,
    calculate_mrr,
    calculate_hit_rate,
    calculate_ndcg_at_k,
    aggregate_metrics,
    calculate_latency_stats,
    save_results,
    print_metrics_table,
    check_metric_target
)


class SystemEvaluator:
    """Evaluator cho hệ thống LegalRAG"""
    
    def __init__(self, config_path='config.json'):
        self.config = load_config(config_path)
        self.api_base_url = self.config['api_base_url']
        self.top_k = self.config['top_k']
        
    def query_system(self, query: str, collection_slug: str = None) -> Dict:
        """
        Gọi API query-service
        
        Returns:
            {
                'answer': str,
                'chunks': List[Dict],
                'processing_time_ms': float,
                'citations': List[str]
            }
        """
        url = f"{self.api_base_url}/query"
        
        payload = {
            'query': query,
            'session_id': 'evaluation_session'
        }
        
        if collection_slug:
            payload['collection_slug'] = collection_slug
        
        try:
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=30)
            elapsed_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse response structure
                # Adjust based on your actual API response format
                return {
                    'answer': data.get('answer', ''),
                    'chunks': data.get('chunks', []),
                    'processing_time_ms': elapsed_ms,
                    'citations': data.get('citations', []),
                    'metadata': data.get('metadata', {})
                }
            else:
                print(f"API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Query failed: {e}")
            return None
    
    def evaluate_single_query(self, test_case: Dict) -> Dict:
        """
        Evaluate một query
        
        Returns:
            {
                'query_id': int,
                'retrieval_metrics': Dict,
                'performance_metrics': Dict,
                'success': bool
            }
        """
        query_id = test_case['id']
        query = test_case['query']
        collection = test_case.get('collection')
        relevant_ids = set(test_case.get('relevant_chunk_ids', []))
        relevance_scores = test_case.get('relevance_scores', {})
        
        # Query system
        response = self.query_system(query, collection)
        
        if not response:
            return {
                'query_id': query_id,
                'success': False,
                'error': 'API call failed'
            }
        
        # Extract retrieved chunk IDs
        retrieved_chunks = response.get('chunks', [])
        retrieved_ids = [chunk.get('id') or chunk.get('chunk_id') for chunk in retrieved_chunks]
        
        # Calculate retrieval metrics
        retrieval_metrics = {}
        
        if relevant_ids:  # Chỉ tính nếu có ground truth
            retrieval_metrics = {
                'precision@5': calculate_precision_at_k(retrieved_ids, relevant_ids, k=5),
                'recall@5': calculate_recall_at_k(retrieved_ids, relevant_ids, k=5),
                'mrr': calculate_mrr(retrieved_ids, relevant_ids),
                'hit_rate@5': calculate_hit_rate(retrieved_ids, relevant_ids, k=5),
            }
            
            if relevance_scores:
                retrieval_metrics['ndcg@5'] = calculate_ndcg_at_k(
                    retrieved_ids, relevance_scores, k=5
                )
        
        # Performance metrics
        performance_metrics = {
            'latency_ms': response['processing_time_ms'],
            'num_chunks_retrieved': len(retrieved_chunks)
        }
        
        return {
            'query_id': query_id,
            'query': query,
            'success': True,
            'retrieval_metrics': retrieval_metrics,
            'performance_metrics': performance_metrics,
            'retrieved_chunks': retrieved_chunks[:5],  # Top 5 for inspection
            'answer': response.get('answer', '')[:200]  # First 200 chars
        }
    
    def run_evaluation(self, test_set_path='test_set.json') -> Dict:
        """
        Chạy evaluation trên toàn bộ test set
        
        Returns:
            {
                'summary': Dict,
                'per_query_results': List[Dict]
            }
        """
        print("=" * 60)
        print("  STARTING EVALUATION")
        print("=" * 60)
        
        # Load test set
        test_set = load_test_set(test_set_path)
        queries = test_set['queries']
        
        print(f"\nTotal test cases: {len(queries)}")
        print(f"API endpoint: {self.api_base_url}")
        print(f"Top-K: {self.top_k}\n")
        
        # Evaluate each query
        results = []
        
        for test_case in tqdm(queries, desc="Evaluating queries"):
            result = self.evaluate_single_query(test_case)
            results.append(result)
            time.sleep(0.5)  # Rate limiting
        
        # Aggregate metrics
        successful_results = [r for r in results if r.get('success')]
        
        if not successful_results:
            print("\n❌ No successful queries. Check API connection.")
            return None
        
        print(f"\n✅ Successful queries: {len(successful_results)}/{len(queries)}")
        
        # Aggregate retrieval metrics
        retrieval_metrics_list = [
            r['retrieval_metrics'] 
            for r in successful_results 
            if r.get('retrieval_metrics')
        ]
        
        aggregated_retrieval = {}
        if retrieval_metrics_list:
            metric_names = retrieval_metrics_list[0].keys()
            for metric_name in metric_names:
                values = [m[metric_name] for m in retrieval_metrics_list]
                aggregated_retrieval[metric_name] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values)
                }
        
        # Aggregate performance metrics
        latencies = [r['performance_metrics']['latency_ms'] for r in successful_results]
        latency_stats = calculate_latency_stats(latencies)
        
        # Summary
        summary = {
            'total_queries': len(queries),
            'successful_queries': len(successful_results),
            'failed_queries': len(queries) - len(successful_results),
            'retrieval_metrics': aggregated_retrieval,
            'performance_metrics': {
                'latency': latency_stats
            },
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return {
            'summary': summary,
            'per_query_results': results
        }


def print_summary_report(results: Dict):
    """
    In báo cáo tóm tắt ra console
    """
    summary = results['summary']
    
    print("\n" + "=" * 60)
    print("  EVALUATION SUMMARY")
    print("=" * 60)
    
    # Overview
    print(f"\n📊 OVERVIEW:")
    print(f"  Total Queries:      {summary['total_queries']}")
    print(f"  Successful:         {summary['successful_queries']} ✅")
    print(f"  Failed:             {summary['failed_queries']}")
    
    # Retrieval metrics
    if summary['retrieval_metrics']:
        print(f"\n📈 RETRIEVAL METRICS:")
        
        targets = {
            'precision@5': 0.7,
            'recall@5': 0.7,
            'mrr': 0.7,
            'hit_rate@5': 0.9,
            'ndcg@5': 0.8
        }
        
        for metric_name, stats in summary['retrieval_metrics'].items():
            mean = stats['mean']
            std = stats['std']
            target = targets.get(metric_name, 0.7)
            status = check_metric_target(mean, target)
            
            print(f"  {metric_name:15s}: {mean:.3f} ± {std:.3f}  "
                  f"(target: >{target:.1f}) {status}")
    
    # Performance
    latency_stats = summary['performance_metrics']['latency']
    print(f"\n⚡ PERFORMANCE:")
    print(f"  Avg Latency:    {latency_stats['mean']:.0f} ms")
    print(f"  Median Latency: {latency_stats['median']:.0f} ms")
    print(f"  P95 Latency:    {latency_stats['p95']:.0f} ms")
    print(f"  P99 Latency:    {latency_stats['p99']:.0f} ms")
    
    target_latency = 5000
    status = check_metric_target(latency_stats['mean'], target_latency, higher_is_better=False)
    print(f"  Target (<5000ms): {status}")
    
    print("\n" + "=" * 60)


def save_summary_text(results: Dict, output_path='evaluation_summary.txt'):
    """
    Lưu báo cáo dạng text file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("  LegalRAG SYSTEM - EVALUATION REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        summary = results['summary']
        
        f.write(f"Generated: {summary['timestamp']}\n")
        f.write(f"Total Queries: {summary['total_queries']}\n")
        f.write(f"Successful: {summary['successful_queries']}\n\n")
        
        # Retrieval metrics
        f.write("RETRIEVAL METRICS\n")
        f.write("-" * 60 + "\n")
        
        for metric_name, stats in summary['retrieval_metrics'].items():
            f.write(f"{metric_name:20s}: {stats['mean']:.3f} ± {stats['std']:.3f}\n")
        
        # Performance
        f.write("\nPERFORMANCE METRICS\n")
        f.write("-" * 60 + "\n")
        
        latency_stats = summary['performance_metrics']['latency']
        f.write(f"Avg Latency:    {latency_stats['mean']:.0f} ms\n")
        f.write(f"Median Latency: {latency_stats['median']:.0f} ms\n")
        f.write(f"P95 Latency:    {latency_stats['p95']:.0f} ms\n")
        f.write(f"P99 Latency:    {latency_stats['p99']:.0f} ms\n")
        
    print(f"\n📄 Summary saved to {output_path}")


def main():
    """Main function"""
    
    # Initialize evaluator
    evaluator = SystemEvaluator()
    
    # Run evaluation
    results = evaluator.run_evaluation()
    
    if not results:
        print("\n❌ Evaluation failed. Exiting.")
        return
    
    # Print summary
    print_summary_report(results)
    
    # Save results
    save_results(results, 'evaluation_results.json')
    save_summary_text(results, 'evaluation_summary.txt')
    
    print("\n✅ Evaluation completed!")
    print("   - evaluation_results.json: Chi tiết results")
    print("   - evaluation_summary.txt: Tóm tắt metrics")


if __name__ == '__main__':
    main()
