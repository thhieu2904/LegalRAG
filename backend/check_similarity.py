#!/usr/bin/env python3
"""
Script kiểm tra mức độ tương đồng giữa các câu hỏi trong questions.json files
Để đảm bảo không có copy-paste và các câu hỏi đa dạng semantic
"""

import json
import os
import glob
from collections import defaultdict
import re
from difflib import SequenceMatcher

def load_questions_from_file(file_path):
    """Load questions từ file JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('main_question', ''), data.get('question_variants', [])
    except Exception as e:
        print(f"❌ Lỗi đọc file {file_path}: {e}")
        return "", []

def clean_text(text):
    """Làm sạch text để so sánh"""
    # Loại bỏ dấu câu và chuyển về chữ thường
    text = re.sub(r'[^\w\s]', '', text.lower())
    # Loại bỏ khoảng trắng thừa
    text = ' '.join(text.split())
    return text

def calculate_similarity(text1, text2):
    """Tính độ tương đồng giữa 2 text"""
    clean1 = clean_text(text1)
    clean2 = clean_text(text2)
    
    if not clean1 or not clean2:
        return 0.0
    
    # Sử dụng SequenceMatcher để tính similarity
    similarity = SequenceMatcher(None, clean1, clean2).ratio()
    return similarity

def check_similarity_within_file(main_question, variants):
    """Kiểm tra similarity trong cùng 1 file"""
    results = []
    
    # So sánh main_question với từng variant
    for i, variant in enumerate(variants):
        sim = calculate_similarity(main_question, variant)
        if sim > 0.8:  # Ngưỡng cao - có thể copy-paste
            results.append({
                'type': 'main_vs_variant',
                'main': main_question,
                'variant': variant,
                'similarity': sim,
                'warning': '⚠️ CÓ THỂ COPY-PASTE'
            })
    
    # So sánh các variants với nhau
    for i in range(len(variants)):
        for j in range(i + 1, len(variants)):
            sim = calculate_similarity(variants[i], variants[j])
            if sim > 0.85:  # Ngưỡng rất cao - chắc chắn copy-paste
                results.append({
                    'type': 'variant_vs_variant',
                    'variant1': variants[i],
                    'variant2': variants[j],
                    'similarity': sim,
                    'warning': '🚨 CHẮC CHẮN COPY-PASTE'
                })
            elif sim > 0.7:  # Ngưỡng trung bình - cần kiểm tra
                results.append({
                    'type': 'variant_vs_variant',
                    'variant1': variants[i],
                    'variant2': variants[j],
                    'similarity': sim,
                    'warning': '⚠️ CẦN KIỂM TRA'
                })
    
    return results

def check_similarity_across_files(all_questions):
    """Kiểm tra similarity giữa các files khác nhau"""
    results = []
    
    file_names = list(all_questions.keys())
    
    for i in range(len(file_names)):
        for j in range(i + 1, len(file_names)):
            file1, file2 = file_names[i], file_names[j]
            
            # So sánh main questions
            main1 = all_questions[file1]['main']
            main2 = all_questions[file2]['main']
            sim_main = calculate_similarity(main1, main2)
            
            if sim_main > 0.7:
                results.append({
                    'type': 'cross_file_main',
                    'file1': file1,
                    'file2': file2,
                    'main1': main1,
                    'main2': main2,
                    'similarity': sim_main,
                    'warning': '⚠️ MAIN QUESTIONS TƯƠNG TỰ'
                })
            
            # So sánh variants giữa 2 files
            variants1 = all_questions[file1]['variants']
            variants2 = all_questions[file2]['variants']
            
            for v1 in variants1:
                for v2 in variants2:
                    sim = calculate_similarity(v1, v2)
                    if sim > 0.85:
                        results.append({
                            'type': 'cross_file_variant',
                            'file1': file1,
                            'file2': file2,
                            'variant1': v1,
                            'variant2': v2,
                            'similarity': sim,
                            'warning': '🚨 VARIANTS GIỐNG HỆT GIỮA 2 FILES'
                        })
    
    return results

def analyze_question_diversity(variants):
    """Phân tích độ đa dạng của variants"""
    if not variants:
        return {'count': 0, 'avg_length': 0, 'unique_words': 0}
    
    # Đếm số variants
    count = len(variants)
    
    # Độ dài trung bình
    lengths = [len(v) for v in variants]
    avg_length = sum(lengths) / len(lengths)
    
    # Số từ unique
    all_words = set()
    for variant in variants:
        words = clean_text(variant).split()
        all_words.update(words)
    
    return {
        'count': count,
        'avg_length': round(avg_length, 1),
        'unique_words': len(all_words)
    }

def main():
    print("🔍 KIỂM TRA MỨC ĐỘ TƯƠNG ĐỒNG TRONG QUESTIONS.JSON FILES")
    print("=" * 80)
    
    # Tìm tất cả questions.json files
    pattern = "data/storage/collections/*/documents/*/questions.json"
    question_files = glob.glob(pattern)
    
    if not question_files:
        print("❌ Không tìm thấy questions.json files!")
        return
    
    print(f"📁 Tìm thấy {len(question_files)} questions.json files")
    print()
    
    all_questions = {}
    all_issues = []
    total_variants = 0
    
    # Load và kiểm tra từng file
    for file_path in sorted(question_files):
        print(f"📖 Đang kiểm tra: {file_path}")
        
        main_q, variants = load_questions_from_file(file_path)
        if not main_q:
            continue
        
        # Lưu để so sánh cross-file
        file_key = os.path.basename(os.path.dirname(file_path))
        all_questions[file_key] = {
            'main': main_q,
            'variants': variants,
            'path': file_path
        }
        
        # Kiểm tra similarity trong file
        issues = check_similarity_within_file(main_q, variants)
        if issues:
            all_issues.extend(issues)
            print(f"   ❌ Tìm thấy {len(issues)} vấn đề")
        else:
            print(f"   ✅ Không có vấn đề")
        
        # Phân tích độ đa dạng
        diversity = analyze_question_diversity(variants)
        total_variants += diversity['count']
        
        print(f"   📊 Variants: {diversity['count']}, Độ dài TB: {diversity['avg_length']} ký tự")
        print()
    
    # Kiểm tra similarity cross-file
    print("🔍 KIỂM TRA TƯƠNG ĐỒNG GIỮA CÁC FILES...")
    cross_file_issues = check_similarity_across_files(all_questions)
    all_issues.extend(cross_file_issues)
    
    # Tổng kết
    print("=" * 80)
    print("📊 TỔNG KẾT KIỂM TRA:")
    print(f"   📁 Tổng số files: {len(question_files)}")
    print(f"   📝 Tổng số variants: {total_variants}")
    print(f"   ❌ Tổng số vấn đề: {len(all_issues)}")
    
    if all_issues:
        print("\n🚨 CHI TIẾT CÁC VẤN ĐỀ TÌM THẤY:")
        print("-" * 80)
        
        # Nhóm theo loại vấn đề
        issues_by_type = defaultdict(list)
        for issue in all_issues:
            issues_by_type[issue['type']].append(issue)
        
        for issue_type, issues in issues_by_type.items():
            print(f"\n📋 {issue_type.upper()}: {len(issues)} vấn đề")
            for i, issue in enumerate(issues[:5], 1):  # Chỉ hiển thị 5 đầu tiên
                print(f"   {i}. {issue['warning']} (Similarity: {issue['similarity']:.3f})")
                if issue_type == 'variant_vs_variant':
                    print(f"      V1: {issue['variant1'][:60]}...")
                    print(f"      V2: {issue['variant2'][:60]}...")
                elif issue_type == 'cross_file_variant':
                    print(f"      File1: {issue['file1']} - {issue['variant1'][:50]}...")
                    print(f"      File2: {issue['file2']} - {issue['variant2'][:50]}...")
                print()
            
            if len(issues) > 5:
                print(f"      ... và {len(issues) - 5} vấn đề khác")
    else:
        print("\n🎉 TẤT CẢ FILES ĐỀU TỐT! KHÔNG CÓ VẤN ĐỀ VỀ COPY-PASTE")
    
    # Đánh giá tổng thể
    print("\n⭐ ĐÁNH GIÁ TỔNG THỂ:")
    if len(all_issues) == 0:
        print("   🏆 XUẤT SẮC: Hệ thống questions đa dạng và semantic hoàn hảo!")
    elif len(all_issues) <= 5:
        print("   🥇 TỐT: Chỉ có vài vấn đề nhỏ, dễ sửa")
    elif len(all_issues) <= 15:
        print("   🥈 KHÁ: Có một số vấn đề cần chú ý")
    else:
        print("   ⚠️ CẦN CẢI THIỆN: Nhiều vấn đề copy-paste cần xử lý")

if __name__ == "__main__":
    main()

