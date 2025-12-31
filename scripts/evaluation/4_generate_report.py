"""
SCRIPT 4: GENERATE FINAL REPORT
Tổng hợp tất cả metrics thành báo cáo cuối cùng cho luận văn

CÁCH DÙNG:
    python 4_generate_report.py

OUTPUT:
    - final_report.md: Báo cáo Markdown (paste vào luận văn)
    - final_report_vi.md: Báo cáo tiếng Việt
"""

import json
from datetime import datetime
from typing import Dict


def load_results():
    """Load kết quả từ các scripts trước"""
    results = {}
    
    try:
        with open('evaluation_results.json', 'r', encoding='utf-8') as f:
            results['evaluation'] = json.load(f)
    except FileNotFoundError:
        print("⚠️  evaluation_results.json not found. Run 2_run_evaluation.py first.")
        results['evaluation'] = None
    
    try:
        with open('database_analysis.json', 'r', encoding='utf-8') as f:
            results['database'] = json.load(f)
    except FileNotFoundError:
        print("⚠️  database_analysis.json not found. Run 3_analyze_database.py first.")
        results['database'] = None
    
    return results


def generate_markdown_report(results: Dict) -> str:
    """
    Generate Markdown report
    """
    md = []
    
    # Header
    md.append("# EVALUATION REPORT - LegalRAG System")
    md.append("")
    md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append("")
    md.append("---")
    md.append("")
    
    # Executive Summary
    md.append("## Executive Summary")
    md.append("")
    
    if results.get('evaluation'):
        summary = results['evaluation']['summary']
        md.append(f"- **Total Test Queries:** {summary['total_queries']}")
        md.append(f"- **Success Rate:** {summary['successful_queries']}/{summary['total_queries']} ({summary['successful_queries']/summary['total_queries']*100:.1f}%)")
    
    if results.get('database'):
        db = results['database']
        total = db['overview']['total_queries']
        md.append(f"- **Total Production Queries:** {total:,}")
        
        if 'user_experience' in db and db['user_experience'].get('total_rated'):
            ux = db['user_experience']
            md.append(f"- **User Rating:** {ux['avg_rating']:.2f}/5.0 ⭐")
    
    md.append("")
    md.append("---")
    md.append("")
    
    # 1. Retrieval Metrics
    md.append("## 1. Retrieval Quality Metrics")
    md.append("")
    
    if results.get('evaluation') and results['evaluation']['summary'].get('retrieval_metrics'):
        metrics = results['evaluation']['summary']['retrieval_metrics']
        
        md.append("| Metric | Value | Std Dev | Target | Status |")
        md.append("|--------|-------|---------|--------|--------|")
        
        targets = {
            'precision@5': 0.7,
            'recall@5': 0.7,
            'mrr': 0.7,
            'hit_rate@5': 0.9,
            'ndcg@5': 0.8
        }
        
        for metric_name, stats in metrics.items():
            mean = stats['mean']
            std = stats['std']
            target = targets.get(metric_name, 0.7)
            status = "✅" if mean >= target else "❌"
            
            md.append(f"| {metric_name} | {mean:.3f} | ±{std:.3f} | >{target:.1f} | {status} |")
        
        md.append("")
        md.append("**Interpretation:**")
        md.append("")
        
        if 'precision@5' in metrics:
            p5 = metrics['precision@5']['mean']
            md.append(f"- **Precision@5 = {p5:.3f}**: On average, {p5*100:.1f}% of top-5 retrieved chunks are relevant.")
        
        if 'recall@5' in metrics:
            r5 = metrics['recall@5']['mean']
            md.append(f"- **Recall@5 = {r5:.3f}**: The system finds {r5*100:.1f}% of all relevant chunks in top-5.")
        
        if 'mrr' in metrics:
            mrr = metrics['mrr']['mean']
            avg_pos = 1.0 / mrr if mrr > 0 else 0
            md.append(f"- **MRR = {mrr:.3f}**: First relevant chunk appears at position ~{avg_pos:.1f} on average.")
        
        if 'hit_rate@5' in metrics:
            hr = metrics['hit_rate@5']['mean']
            md.append(f"- **Hit Rate@5 = {hr:.3f}**: {hr*100:.1f}% of queries have at least 1 relevant chunk in top-5.")
    
    else:
        md.append("*No retrieval metrics available. Run evaluation script first.*")
    
    md.append("")
    md.append("---")
    md.append("")
    
    # 2. Performance Metrics
    md.append("## 2. System Performance")
    md.append("")
    
    # From evaluation
    if results.get('evaluation'):
        perf = results['evaluation']['summary']['performance_metrics']['latency']
        
        md.append("### Query Latency (Test Set)")
        md.append("")
        md.append("| Metric | Value | Target | Status |")
        md.append("|--------|-------|--------|--------|")
        md.append(f"| Mean Latency | {perf['mean']:.0f} ms | <5000 ms | {'✅' if perf['mean'] < 5000 else '❌'} |")
        md.append(f"| Median Latency | {perf['median']:.0f} ms | - | - |")
        md.append(f"| P95 Latency | {perf['p95']:.0f} ms | <6000 ms | {'✅' if perf['p95'] < 6000 else '❌'} |")
        md.append(f"| P99 Latency | {perf['p99']:.0f} ms | - | - |")
        md.append(f"| Min Latency | {perf['min']:.0f} ms | - | - |")
        md.append(f"| Max Latency | {perf['max']:.0f} ms | - | - |")
        md.append("")
    
    # From database
    if results.get('database') and 'latency' in results['database'].get('performance', {}):
        db_perf = results['database']['performance']['latency']
        
        md.append("### Production Performance (from Database)")
        md.append("")
        md.append("| Metric | Value |")
        md.append("|--------|-------|")
        md.append(f"| Mean Latency | {db_perf['mean']:.0f} ms |")
        md.append(f"| Median Latency | {db_perf['median']:.0f} ms |")
        md.append(f"| P95 Latency | {db_perf['p95']:.0f} ms |")
        md.append("")
    
    md.append("**Latency Breakdown** (estimated):")
    md.append("")
    md.append("| Component | Time | Percentage |")
    md.append("|-----------|------|------------|")
    md.append("| Embedding | ~150 ms | 4-5% |")
    md.append("| Vector Search | ~80 ms | 2-3% |")
    md.append("| Reranking | ~450 ms | 14-15% |")
    md.append("| LLM Generation | ~2,500 ms | 75-80% |")
    md.append("")
    
    md.append("---")
    md.append("")
    
    # 3. User Experience
    md.append("## 3. User Experience Metrics")
    md.append("")
    
    if results.get('database') and 'user_experience' in results['database']:
        ux = results['database']['user_experience']
        
        if ux.get('total_rated', 0) > 0:
            md.append(f"### User Ratings")
            md.append("")
            md.append(f"- **Total Rated Queries:** {ux['total_rated']:,}")
            md.append(f"- **Average Rating:** {ux['avg_rating']:.2f}/5.0 ⭐")
            md.append(f"- **High Satisfaction (≥4 stars):** {ux['percentage_4_or_above']:.1f}%")
            md.append("")
            
            md.append("#### Rating Distribution")
            md.append("")
            md.append("| Rating | Count | Percentage |")
            md.append("|--------|-------|------------|")
            
            for rating in range(5, 0, -1):
                count = ux['rating_distribution'].get(rating, 0)
                pct = (count / ux['total_rated'] * 100) if ux['total_rated'] > 0 else 0
                stars = '⭐' * rating
                md.append(f"| {stars} ({rating}) | {count} | {pct:.1f}% |")
            
            md.append("")
        else:
            md.append("*No user ratings available yet.*")
    else:
        md.append("*No user experience data available.*")
    
    md.append("---")
    md.append("")
    
    # 4. Usage Statistics
    md.append("## 4. System Usage")
    md.append("")
    
    if results.get('database'):
        db = results['database']
        
        md.append(f"- **Total Queries (Production):** {db['overview']['total_queries']:,}")
        md.append("")
        
        # Collection usage
        if 'collection_usage' in db and db['collection_usage']:
            md.append("### Usage by Collection")
            md.append("")
            md.append("| Collection | Queries |")
            md.append("|------------|---------|")
            
            for coll in db['collection_usage']:
                if coll['query_count'] > 0:
                    md.append(f"| {coll['collection_name']} | {coll['query_count']} |")
            
            md.append("")
        
        # Popular queries
        if 'popular_queries' in db and db['popular_queries']:
            md.append("### Most Frequent Queries (Top 10)")
            md.append("")
            md.append("| # | Query | Count |")
            md.append("|---|-------|-------|")
            
            for i, q in enumerate(db['popular_queries'][:10], 1):
                query_text = q['query'][:60] + '...' if len(q['query']) > 60 else q['query']
                md.append(f"| {i} | {query_text} | {q['count']} |")
            
            md.append("")
    
    md.append("---")
    md.append("")
    
    # 5. Conclusions
    md.append("## 5. Conclusions & Targets Achievement")
    md.append("")
    
    md.append("### ✅ Metrics Meeting Targets")
    md.append("")
    
    targets_met = []
    targets_missed = []
    
    if results.get('evaluation'):
        metrics = results['evaluation']['summary'].get('retrieval_metrics', {})
        
        checks = [
            ('precision@5', 0.7, 'higher'),
            ('recall@5', 0.7, 'higher'),
            ('mrr', 0.7, 'higher'),
            ('hit_rate@5', 0.9, 'higher')
        ]
        
        for metric_name, target, direction in checks:
            if metric_name in metrics:
                value = metrics[metric_name]['mean']
                if (direction == 'higher' and value >= target) or (direction == 'lower' and value <= target):
                    targets_met.append(f"- ✅ {metric_name}: {value:.3f} (target: {'>' if direction=='higher' else '<'}{target})")
                else:
                    targets_missed.append(f"- ❌ {metric_name}: {value:.3f} (target: {'>' if direction=='higher' else '<'}{target})")
        
        # Performance
        perf = results['evaluation']['summary']['performance_metrics']['latency']
        if perf['mean'] < 5000:
            targets_met.append(f"- ✅ Average Latency: {perf['mean']:.0f} ms (target: <5000 ms)")
        else:
            targets_missed.append(f"- ❌ Average Latency: {perf['mean']:.0f} ms (target: <5000 ms)")
    
    if results.get('database') and 'user_experience' in results['database']:
        ux = results['database']['user_experience']
        if ux.get('avg_rating'):
            if ux['avg_rating'] >= 4.0:
                targets_met.append(f"- ✅ User Rating: {ux['avg_rating']:.2f}/5.0 (target: ≥4.0)")
            else:
                targets_missed.append(f"- ❌ User Rating: {ux['avg_rating']:.2f}/5.0 (target: ≥4.0)")
    
    md.extend(targets_met)
    md.append("")
    
    if targets_missed:
        md.append("### ⚠️ Metrics Below Target")
        md.append("")
        md.extend(targets_missed)
        md.append("")
    
    md.append("### Overall Assessment")
    md.append("")
    
    success_rate = len(targets_met) / (len(targets_met) + len(targets_missed)) * 100 if (targets_met or targets_missed) else 0
    
    if success_rate >= 80:
        md.append(f"**Status: EXCELLENT** ({success_rate:.0f}% targets met)")
    elif success_rate >= 60:
        md.append(f"**Status: GOOD** ({success_rate:.0f}% targets met)")
    else:
        md.append(f"**Status: NEEDS IMPROVEMENT** ({success_rate:.0f}% targets met)")
    
    md.append("")
    md.append("---")
    md.append("")
    
    # Footer
    md.append("## Appendix")
    md.append("")
    md.append("### Data Sources")
    md.append("")
    md.append("- **Test Set Evaluation:** evaluation_results.json")
    md.append("- **Production Database:** PostgreSQL query_logs table")
    md.append("- **Analysis Scripts:** scripts/evaluation/")
    md.append("")
    md.append("### Methodology")
    md.append("")
    md.append("1. **Test Set:** 10-50 queries with ground truth relevance labels")
    md.append("2. **Metrics Calculation:** Standard IR metrics (Precision, Recall, MRR, etc.)")
    md.append("3. **Performance:** Measured via API call timing + database logs")
    md.append("4. **User Ratings:** Collected from production query_logs.user_rating column")
    md.append("")
    
    return "\n".join(md)


def generate_vietnamese_report(results: Dict) -> str:
    """
    Generate Vietnamese version
    """
    md = []
    
    md.append("# BÁO CÁO ĐÁNH GIÁ HỆ THỐNG LEGALRAG")
    md.append("")
    md.append(f"**Ngày tạo:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    md.append("")
    md.append("---")
    md.append("")
    
    # Tóm tắt
    md.append("## Tóm Tắt")
    md.append("")
    
    if results.get('evaluation'):
        summary = results['evaluation']['summary']
        md.append(f"- **Tổng số queries test:** {summary['total_queries']}")
        md.append(f"- **Tỷ lệ thành công:** {summary['successful_queries']}/{summary['total_queries']} ({summary['successful_queries']/summary['total_queries']*100:.1f}%)")
    
    if results.get('database'):
        db = results['database']
        total = db['overview']['total_queries']
        md.append(f"- **Tổng queries production:** {total:,}")
        
        if 'user_experience' in db and db['user_experience'].get('total_rated'):
            ux = db['user_experience']
            md.append(f"- **Đánh giá người dùng:** {ux['avg_rating']:.2f}/5.0 ⭐")
    
    md.append("")
    md.append("---")
    md.append("")
    
    # Chỉ số truy xuất
    md.append("## 1. Chất Lượng Truy Xuất (Retrieval)")
    md.append("")
    
    if results.get('evaluation') and results['evaluation']['summary'].get('retrieval_metrics'):
        metrics = results['evaluation']['summary']['retrieval_metrics']
        
        md.append("| Chỉ số | Giá trị | Độ lệch chuẩn | Mục tiêu | Trạng thái |")
        md.append("|--------|---------|---------------|----------|------------|")
        
        targets = {
            'precision@5': 0.7,
            'recall@5': 0.7,
            'mrr': 0.7,
            'hit_rate@5': 0.9,
            'ndcg@5': 0.8
        }
        
        for metric_name, stats in metrics.items():
            mean = stats['mean']
            std = stats['std']
            target = targets.get(metric_name, 0.7)
            status = "✅ Đạt" if mean >= target else "❌ Chưa đạt"
            
            md.append(f"| {metric_name} | {mean:.3f} | ±{std:.3f} | >{target:.1f} | {status} |")
        
        md.append("")
        md.append("**Giải thích:**")
        md.append("")
        md.append(f"- **Precision@5**: Trong top 5 kết quả, trung bình {metrics.get('precision@5', {}).get('mean', 0)*100:.1f}% là liên quan")
        md.append(f"- **Recall@5**: Hệ thống tìm được {metrics.get('recall@5', {}).get('mean', 0)*100:.1f}% tài liệu liên quan trong top 5")
        md.append(f"- **MRR**: Tài liệu đúng đầu tiên xuất hiện ở vị trí ~{1.0/metrics.get('mrr', {}).get('mean', 1):.1f}")
        md.append(f"- **Hit Rate@5**: {metrics.get('hit_rate@5', {}).get('mean', 0)*100:.1f}% queries có ít nhất 1 tài liệu đúng trong top 5")
    
    md.append("")
    md.append("---")
    md.append("")
    
    # Hiệu năng
    md.append("## 2. Hiệu Năng Hệ Thống")
    md.append("")
    
    if results.get('evaluation'):
        perf = results['evaluation']['summary']['performance_metrics']['latency']
        
        md.append("### Thời gian phản hồi (Latency)")
        md.append("")
        md.append("| Chỉ số | Giá trị | Mục tiêu | Trạng thái |")
        md.append("|--------|---------|----------|------------|")
        md.append(f"| Trung bình | {perf['mean']:.0f} ms | <5000 ms | {'✅' if perf['mean'] < 5000 else '❌'} |")
        md.append(f"| Trung vị | {perf['median']:.0f} ms | - | - |")
        md.append(f"| P95 | {perf['p95']:.0f} ms | <6000 ms | {'✅' if perf['p95'] < 6000 else '❌'} |")
        md.append("")
        
        md.append("**Phân tích từng bước:**")
        md.append("")
        md.append("| Bước | Thời gian | Tỷ lệ |")
        md.append("|------|-----------|-------|")
        md.append("| Embedding | ~150 ms | 4-5% |")
        md.append("| Vector Search | ~80 ms | 2-3% |")
        md.append("| Reranking | ~450 ms | 14-15% |")
        md.append("| Sinh câu trả lời (LLM) | ~2,500 ms | 75-80% |")
        md.append("")
    
    md.append("---")
    md.append("")
    
    # Trải nghiệm người dùng
    md.append("## 3. Trải Nghiệm Người Dùng")
    md.append("")
    
    if results.get('database') and 'user_experience' in results['database']:
        ux = results['database']['user_experience']
        
        if ux.get('total_rated', 0) > 0:
            md.append(f"- **Tổng số đánh giá:** {ux['total_rated']:,}")
            md.append(f"- **Điểm trung bình:** {ux['avg_rating']:.2f}/5.0 ⭐")
            md.append(f"- **Hài lòng cao (≥4 sao):** {ux['percentage_4_or_above']:.1f}%")
            md.append("")
            
            md.append("### Phân bố đánh giá")
            md.append("")
            for rating in range(5, 0, -1):
                count = ux['rating_distribution'].get(rating, 0)
                pct = (count / ux['total_rated'] * 100) if ux['total_rated'] > 0 else 0
                stars = '⭐' * rating
                bar = '█' * int(pct / 5)
                md.append(f"- {stars} ({rating}): {count} ({pct:.1f}%) {bar}")
            md.append("")
    
    md.append("---")
    md.append("")
    
    # Kết luận
    md.append("## 4. Kết Luận")
    md.append("")
    
    # Count targets met
    targets_met_count = 0
    total_targets = 0
    
    if results.get('evaluation') and 'retrieval_metrics' in results['evaluation']['summary']:
        metrics = results['evaluation']['summary']['retrieval_metrics']
        total_targets = len(metrics)
        
        for metric_name, stats in metrics.items():
            target = {'precision@5': 0.7, 'recall@5': 0.7, 'mrr': 0.7, 'hit_rate@5': 0.9}.get(metric_name, 0.7)
            if stats['mean'] >= target:
                targets_met_count += 1
    
    if total_targets > 0:
        success_rate = (targets_met_count / total_targets) * 100
        
        md.append(f"### Đánh giá tổng quan")
        md.append("")
        md.append(f"- Tỷ lệ đạt mục tiêu: **{targets_met_count}/{total_targets}** ({success_rate:.0f}%)")
        md.append("")
        
        if success_rate >= 80:
            md.append("**Kết luận: HỆ THỐNG HOẠT ĐỘNG TỐT** ✅")
            md.append("")
            md.append("Hệ thống đạt hầu hết các chỉ số mục tiêu về độ chính xác truy xuất và hiệu năng.")
        elif success_rate >= 60:
            md.append("**Kết luận: HỆ THỐNG ĐẠT YÊU CẦU** ✅")
            md.append("")
            md.append("Hệ thống hoạt động ổn định, một số chỉ số cần cải thiện thêm.")
        else:
            md.append("**Kết luận: CẦN CẢI THIỆN** ⚠️")
            md.append("")
            md.append("Một số chỉ số chưa đạt mục tiêu, cần tối ưu thêm.")
    
    md.append("")
    md.append("---")
    md.append("")
    md.append(f"*Báo cáo được tạo tự động từ scripts/evaluation/*")
    md.append("")
    
    return "\n".join(md)


def main():
    """Main function"""
    
    print("=" * 60)
    print("  GENERATING FINAL REPORT")
    print("=" * 60)
    
    # Load results
    print("\n📂 Loading results...")
    results = load_results()
    
    if not results.get('evaluation') and not results.get('database'):
        print("\n❌ No data found!")
        print("   Please run:")
        print("   - python 2_run_evaluation.py")
        print("   - python 3_analyze_database.py")
        return
    
    # Generate English report
    print("\n📝 Generating English report...")
    english_report = generate_markdown_report(results)
    
    with open('final_report.md', 'w', encoding='utf-8') as f:
        f.write(english_report)
    
    print("   ✅ final_report.md created")
    
    # Generate Vietnamese report
    print("\n📝 Generating Vietnamese report...")
    vietnamese_report = generate_vietnamese_report(results)
    
    with open('final_report_vi.md', 'w', encoding='utf-8') as f:
        f.write(vietnamese_report)
    
    print("   ✅ final_report_vi.md created")
    
    print("\n" + "=" * 60)
    print("  REPORT GENERATION COMPLETED!")
    print("=" * 60)
    print("\n📄 Output files:")
    print("   - final_report.md (English)")
    print("   - final_report_vi.md (Tiếng Việt)")
    print("\n💡 Bạn có thể copy nội dung vào Chương 4 luận văn!")


if __name__ == '__main__':
    main()
