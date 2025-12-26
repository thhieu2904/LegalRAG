"""
SCRIPT 3: ANALYZE DATABASE
Phân tích query_logs và các bảng khác trong PostgreSQL

CÁCH DÙNG:
    python 3_analyze_database.py

OUTPUT:
    - database_analysis.json: Kết quả phân tích
    - database_analysis.txt: Báo cáo text
"""

import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List

from utils import (
    load_config,
    get_db_connection,
    calculate_latency_stats,
    save_results
)


class DatabaseAnalyzer:
    """Analyzer cho PostgreSQL database"""
    
    def __init__(self, config_path='config.json'):
        self.config = load_config(config_path)
        self.conn = get_db_connection(self.config)
    
    def __del__(self):
        """Close connection"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def get_total_queries(self) -> int:
        """Đếm tổng số queries"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM query_logs")
            return cur.fetchone()['count']
    
    def get_user_ratings_stats(self) -> Dict:
        """
        Phân tích user ratings
        
        Returns:
            {
                'total_rated': int,
                'avg_rating': float,
                'rating_distribution': Dict[int, int],
                'percentage_4_or_above': float
            }
        """
        with self.conn.cursor() as cur:
            # Total rated queries
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM query_logs 
                WHERE user_rating IS NOT NULL
            """)
            total_rated = cur.fetchone()['count']
            
            if total_rated == 0:
                return {
                    'total_rated': 0,
                    'note': 'No ratings found in database'
                }
            
            # Average rating
            cur.execute("""
                SELECT AVG(user_rating) as avg_rating
                FROM query_logs
                WHERE user_rating IS NOT NULL
            """)
            avg_rating = cur.fetchone()['avg_rating']
            
            # Rating distribution
            cur.execute("""
                SELECT user_rating, COUNT(*) as count
                FROM query_logs
                WHERE user_rating IS NOT NULL
                GROUP BY user_rating
                ORDER BY user_rating DESC
            """)
            distribution = {row['user_rating']: row['count'] for row in cur.fetchall()}
            
            # Percentage 4 stars or above
            cur.execute("""
                SELECT COUNT(*) as count
                FROM query_logs
                WHERE user_rating >= 4
            """)
            high_rating_count = cur.fetchone()['count']
            percentage_4_or_above = (high_rating_count / total_rated * 100) if total_rated > 0 else 0
            
            return {
                'total_rated': total_rated,
                'avg_rating': float(avg_rating) if avg_rating else 0,
                'rating_distribution': distribution,
                'percentage_4_or_above': percentage_4_or_above
            }
    
    def get_performance_metrics(self) -> Dict:
        """
        Phân tích performance metrics từ query_logs
        
        Returns:
            {
                'latency': Dict,
                'top_k_distribution': Dict
            }
        """
        with self.conn.cursor() as cur:
            # Latency stats
            cur.execute("""
                SELECT processing_time_ms
                FROM query_logs
                WHERE processing_time_ms IS NOT NULL
            """)
            rows = cur.fetchall()
            
            if not rows:
                return {'note': 'No performance data found'}
            
            latencies = [row['processing_time_ms'] for row in rows]
            latency_stats = calculate_latency_stats(latencies)
            
            # Top-K distribution
            cur.execute("""
                SELECT top_k, COUNT(*) as count
                FROM query_logs
                WHERE top_k IS NOT NULL
                GROUP BY top_k
                ORDER BY top_k
            """)
            top_k_dist = {row['top_k']: row['count'] for row in cur.fetchall()}
            
            return {
                'latency': latency_stats,
                'top_k_distribution': top_k_dist
            }
    
    def get_popular_queries(self, limit=10) -> List[Dict]:
        """
        Lấy các queries phổ biến nhất
        
        Returns:
            List of {'query': str, 'count': int}
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT query, COUNT(*) as count
                FROM query_logs
                GROUP BY query
                ORDER BY count DESC
                LIMIT %s
            """, (limit,))
            
            return [dict(row) for row in cur.fetchall()]
    
    def get_collection_usage(self) -> Dict:
        """
        Phân tích usage theo collection
        
        Returns:
            Dict[collection_id, count]
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    c.name as collection_name,
                    c.slug as collection_slug,
                    COUNT(ql.id) as query_count
                FROM collections c
                LEFT JOIN query_logs ql ON ql.collection_id = c.id
                GROUP BY c.id, c.name, c.slug
                ORDER BY query_count DESC
            """)
            
            return [
                {
                    'collection_name': row['collection_name'],
                    'collection_slug': row['collection_slug'],
                    'query_count': row['query_count']
                }
                for row in cur.fetchall()
            ]
    
    def get_temporal_patterns(self, days=7) -> Dict:
        """
        Phân tích patterns theo thời gian
        
        Returns:
            {
                'daily_query_count': Dict[date, count],
                'hourly_distribution': Dict[hour, count]
            }
        """
        with self.conn.cursor() as cur:
            # Daily query count (last N days)
            cur.execute("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as count
                FROM query_logs
                WHERE created_at >= NOW() - INTERVAL '%s days'
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (days,))
            
            daily_counts = {
                str(row['date']): row['count'] 
                for row in cur.fetchall()
            }
            
            # Hourly distribution
            cur.execute("""
                SELECT 
                    EXTRACT(HOUR FROM created_at) as hour,
                    COUNT(*) as count
                FROM query_logs
                GROUP BY EXTRACT(HOUR FROM created_at)
                ORDER BY hour
            """)
            
            hourly_dist = {
                int(row['hour']): row['count'] 
                for row in cur.fetchall()
            }
            
            return {
                'daily_query_count': daily_counts,
                'hourly_distribution': hourly_dist
            }
    
    def get_error_analysis(self) -> Dict:
        """
        Phân tích errors/failures
        
        Returns:
            {
                'total_errors': int,
                'error_rate': float,
                'error_types': Dict
            }
        """
        with self.conn.cursor() as cur:
            # Total errors (nếu có error_message column)
            try:
                cur.execute("""
                    SELECT COUNT(*) as count
                    FROM query_logs
                    WHERE error_message IS NOT NULL
                """)
                error_count = cur.fetchone()['count']
                
                total_queries = self.get_total_queries()
                error_rate = (error_count / total_queries * 100) if total_queries > 0 else 0
                
                return {
                    'total_errors': error_count,
                    'error_rate_percentage': error_rate,
                    'total_queries': total_queries
                }
            except:
                return {
                    'note': 'No error tracking column found in query_logs'
                }
    
    def analyze_all(self) -> Dict:
        """
        Chạy tất cả analyses
        
        Returns:
            Full analysis report
        """
        print("=" * 60)
        print("  ANALYZING DATABASE")
        print("=" * 60)
        
        print("\n📊 Collecting statistics...")
        
        total_queries = self.get_total_queries()
        print(f"  Total queries: {total_queries}")
        
        ratings = self.get_user_ratings_stats()
        print(f"  Rated queries: {ratings.get('total_rated', 0)}")
        
        performance = self.get_performance_metrics()
        print(f"  Performance metrics: {'✅' if 'latency' in performance else '⚠️'}")
        
        popular = self.get_popular_queries()
        print(f"  Popular queries: {len(popular)}")
        
        collection_usage = self.get_collection_usage()
        print(f"  Collections analyzed: {len(collection_usage)}")
        
        temporal = self.get_temporal_patterns()
        print(f"  Temporal patterns: {'✅' if temporal['daily_query_count'] else '⚠️'}")
        
        errors = self.get_error_analysis()
        
        report = {
            'overview': {
                'total_queries': total_queries,
                'analysis_timestamp': datetime.now().isoformat()
            },
            'user_experience': ratings,
            'performance': performance,
            'popular_queries': popular,
            'collection_usage': collection_usage,
            'temporal_patterns': temporal,
            'errors': errors
        }
        
        return report


def print_analysis_report(report: Dict):
    """
    In báo cáo analysis
    """
    print("\n" + "=" * 60)
    print("  DATABASE ANALYSIS REPORT")
    print("=" * 60)
    
    # Overview
    print(f"\n📊 OVERVIEW:")
    print(f"  Total Queries: {report['overview']['total_queries']:,}")
    
    # User Experience
    if 'user_experience' in report:
        ux = report['user_experience']
        if ux.get('total_rated', 0) > 0:
            print(f"\n⭐ USER EXPERIENCE:")
            print(f"  Total Rated:      {ux['total_rated']:,}")
            print(f"  Avg Rating:       {ux['avg_rating']:.2f}/5.0")
            print(f"  Rating ≥4:        {ux['percentage_4_or_above']:.1f}%")
            
            print(f"\n  Rating Distribution:")
            for rating, count in sorted(ux['rating_distribution'].items(), reverse=True):
                pct = (count / ux['total_rated'] * 100)
                bar = '█' * int(pct / 2)
                print(f"    {rating}⭐: {count:3d} ({pct:5.1f}%) {bar}")
    
    # Performance
    if 'performance' in report and 'latency' in report['performance']:
        perf = report['performance']['latency']
        print(f"\n⚡ PERFORMANCE:")
        print(f"  Avg Latency:    {perf['mean']:.0f} ms")
        print(f"  Median Latency: {perf['median']:.0f} ms")
        print(f"  P95 Latency:    {perf['p95']:.0f} ms")
        print(f"  P99 Latency:    {perf['p99']:.0f} ms")
    
    # Popular queries
    if 'popular_queries' in report and report['popular_queries']:
        print(f"\n🔥 TOP QUERIES:")
        for i, query_data in enumerate(report['popular_queries'][:5], 1):
            query = query_data['query'][:50] + '...' if len(query_data['query']) > 50 else query_data['query']
            print(f"  {i}. {query} ({query_data['count']} times)")
    
    # Collection usage
    if 'collection_usage' in report and report['collection_usage']:
        print(f"\n📚 COLLECTION USAGE:")
        for coll in report['collection_usage']:
            if coll['query_count'] > 0:
                print(f"  {coll['collection_name']:20s}: {coll['query_count']:3d} queries")
    
    print("\n" + "=" * 60)


def save_analysis_text(report: Dict, output_path='database_analysis.txt'):
    """
    Lưu báo cáo dạng text
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("  LegalRAG - DATABASE ANALYSIS REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Generated: {report['overview']['analysis_timestamp']}\n")
        f.write(f"Total Queries: {report['overview']['total_queries']}\n\n")
        
        # User Experience
        if 'user_experience' in report:
            ux = report['user_experience']
            if ux.get('total_rated', 0) > 0:
                f.write("USER EXPERIENCE\n")
                f.write("-" * 60 + "\n")
                f.write(f"Total Rated:      {ux['total_rated']}\n")
                f.write(f"Avg Rating:       {ux['avg_rating']:.2f}/5.0\n")
                f.write(f"Rating ≥4:        {ux['percentage_4_or_above']:.1f}%\n\n")
        
        # Performance
        if 'performance' in report and 'latency' in report['performance']:
            perf = report['performance']['latency']
            f.write("PERFORMANCE METRICS\n")
            f.write("-" * 60 + "\n")
            f.write(f"Avg Latency:    {perf['mean']:.0f} ms\n")
            f.write(f"Median Latency: {perf['median']:.0f} ms\n")
            f.write(f"P95 Latency:    {perf['p95']:.0f} ms\n")
            f.write(f"P99 Latency:    {perf['p99']:.0f} ms\n\n")
    
    print(f"\n📄 Analysis saved to {output_path}")


def main():
    """Main function"""
    
    try:
        # Initialize analyzer
        analyzer = DatabaseAnalyzer()
        
        # Run analysis
        report = analyzer.analyze_all()
        
        # Print report
        print_analysis_report(report)
        
        # Save results
        save_results(report, 'database_analysis.json')
        save_analysis_text(report, 'database_analysis.txt')
        
        print("\n✅ Database analysis completed!")
        print("   - database_analysis.json: Chi tiết")
        print("   - database_analysis.txt: Báo cáo text")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("  1. Check PostgreSQL is running: docker ps")
        print("  2. Check config.json has correct DB credentials")
        print("  3. Check query_logs table exists: psql -U postgres -d legalrag")


if __name__ == '__main__':
    main()
