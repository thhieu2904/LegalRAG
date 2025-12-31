"""
Utility functions for evaluation scripts
"""
import json
import time
from typing import List, Dict, Set, Optional
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor


def load_config(config_path='config.json') -> Dict:
    """Load configuration file"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_db_connection(config: Dict):
    """Create PostgreSQL connection"""
    db_config = config['db_connection']
    return psycopg2.connect(
        host=db_config['host'],
        port=db_config['port'],
        database=db_config['database'],
        user=db_config['user'],
        password=db_config['password'],
        cursor_factory=RealDictCursor
    )


# =============================================================================
# RETRIEVAL METRICS
# =============================================================================

def calculate_precision_at_k(retrieved_ids: List[str], 
                              relevant_ids: Set[str], 
                              k: int) -> float:
    """
    Calculate Precision@K
    
    Args:
        retrieved_ids: List of retrieved chunk IDs (ordered by score)
        relevant_ids: Set of ground truth relevant chunk IDs
        k: Number of top results to consider
    
    Returns:
        Precision@K score (0.0 to 1.0)
    """
    if k == 0 or not retrieved_ids:
        return 0.0
    
    top_k = retrieved_ids[:k]
    relevant_count = sum(1 for chunk_id in top_k if chunk_id in relevant_ids)
    return relevant_count / k


def calculate_recall_at_k(retrieved_ids: List[str], 
                           relevant_ids: Set[str], 
                           k: int) -> float:
    """
    Calculate Recall@K
    
    Args:
        retrieved_ids: List of retrieved chunk IDs
        relevant_ids: Set of ground truth relevant chunk IDs
        k: Number of top results to consider
    
    Returns:
        Recall@K score (0.0 to 1.0)
    """
    if not relevant_ids:
        return 0.0
    
    top_k = retrieved_ids[:k]
    found_count = sum(1 for chunk_id in top_k if chunk_id in relevant_ids)
    return found_count / len(relevant_ids)


def calculate_mrr(retrieved_ids: List[str], 
                  relevant_ids: Set[str]) -> float:
    """
    Calculate Mean Reciprocal Rank (for single query)
    
    Args:
        retrieved_ids: List of retrieved chunk IDs
        relevant_ids: Set of ground truth relevant chunk IDs
    
    Returns:
        Reciprocal Rank (1/position of first relevant doc)
    """
    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def calculate_hit_rate(retrieved_ids: List[str], 
                       relevant_ids: Set[str], 
                       k: int) -> float:
    """
    Calculate Hit Rate@K (binary: có ít nhất 1 relevant doc không)
    
    Returns:
        1.0 if hit, 0.0 if miss
    """
    top_k = retrieved_ids[:k]
    return 1.0 if any(chunk_id in relevant_ids for chunk_id in top_k) else 0.0


def calculate_ndcg_at_k(retrieved_ids: List[str], 
                        relevance_scores: Dict[str, float], 
                        k: int) -> float:
    """
    Calculate NDCG@K (Normalized Discounted Cumulative Gain)
    
    Args:
        retrieved_ids: List of retrieved chunk IDs
        relevance_scores: Dict mapping chunk_id -> relevance score (0-3)
        k: Number of top results
    
    Returns:
        NDCG@K score (0.0 to 1.0)
    """
    def dcg(scores):
        return sum(score / np.log2(i + 2) for i, score in enumerate(scores))
    
    # DCG của retrieved results
    retrieved_scores = [relevance_scores.get(chunk_id, 0) for chunk_id in retrieved_ids[:k]]
    dcg_score = dcg(retrieved_scores)
    
    # IDCG (ideal DCG): sắp xếp theo relevance giảm dần
    ideal_scores = sorted(relevance_scores.values(), reverse=True)[:k]
    idcg_score = dcg(ideal_scores)
    
    return dcg_score / idcg_score if idcg_score > 0 else 0.0


# =============================================================================
# AGGREGATE METRICS
# =============================================================================

def aggregate_metrics(results: List[Dict]) -> Dict:
    """
    Aggregate metrics across multiple queries
    
    Args:
        results: List of per-query results
    
    Returns:
        Aggregated metrics (mean, std, min, max)
    """
    metrics = {}
    
    # Group by metric name
    metric_names = set()
    for result in results:
        metric_names.update(result.keys())
    
    for metric_name in metric_names:
        values = [r.get(metric_name, 0) for r in results]
        metrics[metric_name] = {
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'median': np.median(values)
        }
    
    return metrics


# =============================================================================
# PERFORMANCE METRICS
# =============================================================================

def calculate_latency_stats(latencies: List[float]) -> Dict:
    """
    Calculate latency statistics
    
    Args:
        latencies: List of latency values in milliseconds
    
    Returns:
        Dict with mean, median, p50, p90, p95, p99
    """
    if not latencies:
        return {}
    
    return {
        'mean': np.mean(latencies),
        'median': np.median(latencies),
        'std': np.std(latencies),
        'min': np.min(latencies),
        'max': np.max(latencies),
        'p50': np.percentile(latencies, 50),
        'p90': np.percentile(latencies, 90),
        'p95': np.percentile(latencies, 95),
        'p99': np.percentile(latencies, 99)
    }


# =============================================================================
# FORMATTING & OUTPUT
# =============================================================================

def format_metric_value(value: float, metric_type: str = 'ratio') -> str:
    """
    Format metric value for display
    
    Args:
        value: Metric value
        metric_type: 'ratio' (0-1), 'percentage', 'latency', 'count'
    """
    if metric_type == 'ratio':
        return f"{value:.3f}"
    elif metric_type == 'percentage':
        return f"{value*100:.1f}%"
    elif metric_type == 'latency':
        return f"{value:.0f} ms"
    elif metric_type == 'count':
        return f"{int(value):,}"
    else:
        return f"{value:.2f}"


def print_metrics_table(metrics: Dict, title: str = "METRICS"):
    """
    Print metrics in a formatted table
    """
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)
    
    for metric_name, stats in metrics.items():
        if isinstance(stats, dict):
            mean_val = stats.get('mean', 0)
            std_val = stats.get('std', 0)
            print(f"{metric_name:20s}: {mean_val:.3f} ± {std_val:.3f}")
        else:
            print(f"{metric_name:20s}: {stats:.3f}")
    
    print("=" * 60)


def check_metric_target(value: float, target: float, higher_is_better: bool = True) -> str:
    """
    Check if metric meets target
    
    Returns:
        Status emoji: ✅ (pass) or ❌ (fail)
    """
    if higher_is_better:
        return "✅" if value >= target else "❌"
    else:
        return "✅" if value <= target else "❌"


# =============================================================================
# QUERY HELPERS
# =============================================================================

def measure_query_time(func):
    """
    Decorator to measure function execution time
    """
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed_ms = (time.time() - start) * 1000
        return result, elapsed_ms
    return wrapper


# =============================================================================
# DATA VALIDATION
# =============================================================================

def validate_test_case(test_case: Dict) -> bool:
    """
    Validate test case structure
    """
    required_fields = ['id', 'query', 'relevant_chunk_ids']
    return all(field in test_case for field in required_fields)


def load_test_set(path: str = 'test_set.json') -> Dict:
    """
    Load and validate test set
    """
    with open(path, 'r', encoding='utf-8') as f:
        test_set = json.load(f)
    
    # Validate
    if 'queries' not in test_set:
        raise ValueError("Test set must have 'queries' field")
    
    valid_queries = [q for q in test_set['queries'] if validate_test_case(q)]
    
    print(f"Loaded {len(valid_queries)} valid test cases")
    
    return {'queries': valid_queries}


def save_results(results: Dict, output_path: str = 'evaluation_results.json'):
    """
    Save evaluation results to JSON file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Results saved to {output_path}")
