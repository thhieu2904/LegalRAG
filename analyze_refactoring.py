#!/usr/bin/env python3
"""
RAG Engine Refactoring Analysis
Phân tích và đề xuất cách chia nhỏ file rag_engine.py (1288 dòng)
"""

import os
import re
from collections import defaultdict

def analyze_rag_engine_structure():
    """Phân tích cấu trúc file rag_engine.py"""
    print("🔍 RAG Engine Structure Analysis")
    print("=" * 60)
    
    file_path = "backend/app/services/rag_engine.py"
    
    if not os.path.exists(file_path):
        print("❌ File not found")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    total_lines = len(lines)
    print(f"📊 Total lines: {total_lines}")
    
    # Analyze classes and methods
    classes = []
    methods = []
    private_methods = []
    
    class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    method_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Find classes
        class_match = re.match(class_pattern, stripped)
        if class_match:
            classes.append({
                'name': class_match.group(1),
                'line': line_num,
                'type': 'class'
            })
        
        # Find methods
        method_match = re.match(method_pattern, stripped)
        if method_match:
            method_name = method_match.group(1)
            if method_name.startswith('_'):
                private_methods.append({
                    'name': method_name,
                    'line': line_num,
                    'type': 'private_method'
                })
            else:
                methods.append({
                    'name': method_name,
                    'line': line_num,
                    'type': 'public_method'
                })
    
    print(f"📋 Classes: {len(classes)}")
    for cls in classes:
        print(f"   - {cls['name']} (line {cls['line']})")
    
    print(f"\n📋 Public Methods: {len(methods)}")
    for method in methods[:10]:  # Show first 10
        print(f"   - {method['name']} (line {method['line']})")
    if len(methods) > 10:
        print(f"   ... and {len(methods) - 10} more")
    
    print(f"\n📋 Private Methods: {len(private_methods)}")
    for method in private_methods:
        print(f"   - {method['name']} (line {method['line']})")
    
    return {
        'total_lines': total_lines,
        'classes': classes,
        'public_methods': methods,
        'private_methods': private_methods
    }

def identify_concerns():
    """Xác định các concerns chính trong file"""
    print("\n🎯 Identifying Main Concerns")
    print("=" * 50)
    
    file_path = "backend/app/services/rag_engine.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    concerns = {
        'Session Management': [
            'create_session', 'get_session', 'cleanup_old_sessions', 
            'OptimizedChatSession', 'chat_sessions'
        ],
        'Clarification Flow': [
            'handle_clarification', '_generate_smart_clarification',
            'clarification', 'proceed_with_collection', 'proceed_with_document'
        ],
        'RAG Engine Core': [
            'enhanced_query', '_generate_answer_with_context', 
            '_build_context_from_expanded', 'broad_search'
        ],
        'Smart Routing': [
            'smart_router', 'routing_result', 'confidence_level',
            'route_query', 'inferred_filters'
        ],
        'Vector Search': [
            'vectordb_service', 'similarity_threshold', 'search_results',
            'rerank', 'expand_context'
        ],
        'LLM Integration': [
            'llm_service', 'generate_response', 'prompt_template',
            'temperature', 'max_tokens'
        ]
    }
    
    concern_scores = {}
    
    for concern, keywords in concerns.items():
        score = 0
        found_keywords = []
        
        for keyword in keywords:
            matches = len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE))
            score += matches
            if matches > 0:
                found_keywords.append(f"{keyword}({matches})")
        
        concern_scores[concern] = {
            'score': score,
            'keywords': found_keywords
        }
    
    # Sort by score
    sorted_concerns = sorted(concern_scores.items(), key=lambda x: x[1]['score'], reverse=True)
    
    for concern, data in sorted_concerns:
        print(f"📌 {concern}: Score {data['score']}")
        if data['keywords']:
            print(f"   Keywords: {', '.join(data['keywords'][:5])}")
            if len(data['keywords']) > 5:
                print(f"   ... and {len(data['keywords']) - 5} more")
        print()
    
    return concern_scores

def suggest_refactoring_plan():
    """Đề xuất kế hoạch refactoring"""
    print("🔧 Refactoring Suggestions")
    print("=" * 50)
    
    suggestions = [
        {
            'priority': 'HIGH',
            'component': 'ClarificationFlowService',
            'description': 'Extract 3-step clarification logic',
            'methods': [
                'handle_clarification',
                '_generate_smart_clarification',
                '_generate_document_clarification',
                '_generate_question_clarification'
            ],
            'benefits': [
                'Easier to test clarification flow',
                'Cleaner separation of concerns',
                'Reusable clarification logic'
            ],
            'estimated_lines': '300-400 lines'
        },
        {
            'priority': 'MEDIUM',
            'component': 'SessionManagerService',
            'description': 'Extract session management logic',
            'methods': [
                'create_session',
                'get_session',
                'cleanup_old_sessions',
                'OptimizedChatSession class'
            ],
            'benefits': [
                'Reusable across services',
                'Easier session testing',
                'Better session monitoring'
            ],
            'estimated_lines': '200-250 lines'
        },
        {
            'priority': 'MEDIUM',
            'component': 'ContextBuilderService',
            'description': 'Extract context building and expansion',
            'methods': [
                '_build_context_from_expanded',
                '_generate_answer_with_context',
                'context expansion logic'
            ],
            'benefits': [
                'Better context testing',
                'Reusable context logic',
                'Performance optimization'
            ],
            'estimated_lines': '200-300 lines'
        },
        {
            'priority': 'LOW',
            'component': 'RAGCoreService',
            'description': 'Keep core RAG logic together',
            'methods': [
                'enhanced_query (simplified)',
                'query',
                'get_health_status'
            ],
            'benefits': [
                'Main orchestration logic',
                'Integration point',
                'Performance monitoring'
            ],
            'estimated_lines': '400-500 lines'
        }
    ]
    
    print("📋 Suggested Component Breakdown:")
    print()
    
    for suggestion in suggestions:
        print(f"🏷️  {suggestion['component']} ({suggestion['priority']} Priority)")
        print(f"   📝 Description: {suggestion['description']}")
        print(f"   📊 Estimated size: {suggestion['estimated_lines']}")
        print(f"   🔧 Methods to extract:")
        for method in suggestion['methods']:
            print(f"      - {method}")
        print(f"   ✅ Benefits:")
        for benefit in suggestion['benefits']:
            print(f"      - {benefit}")
        print()
    
    return suggestions

def assess_refactoring_priority():
    """Đánh giá mức độ ưu tiên refactoring"""
    print("⚖️  Refactoring Priority Assessment")
    print("=" * 50)
    
    current_state = {
        'pros': [
            '✅ System is working well',
            '✅ All features implemented',
            '✅ Good performance',
            '✅ Comprehensive functionality',
            '✅ Battle-tested in production'
        ],
        'cons': [
            '❌ File too large (1288 lines)',
            '❌ Multiple responsibilities',
            '❌ Hard to review changes',
            '❌ Testing complexity',
            '❌ Future maintenance challenges',
            '❌ Code duplication potential'
        ]
    }
    
    risk_factors = {
        'HIGH': [
            'Adding new features will be complex',
            'Bug fixes might introduce regressions',
            'Code reviews take too long'
        ],
        'MEDIUM': [
            'New team members need longer onboarding',
            'Parallel development conflicts',
            'Testing coverage gaps'
        ],
        'LOW': [
            'Performance optimization harder',
            'Documentation maintenance'
        ]
    }
    
    recommendations = {
        'IMMEDIATE (Next Sprint)': [
            'Create refactoring plan document',
            'Add comprehensive unit tests for current code',
            'Document current architecture'
        ],
        'SHORT TERM (1-2 months)': [
            'Extract ClarificationFlowService (highest ROI)',
            'Extract SessionManagerService',
            'Create interface contracts'
        ],
        'LONG TERM (3-6 months)': [
            'Extract ContextBuilderService',
            'Optimize core RAG orchestration',
            'Performance benchmarking'
        ]
    }
    
    print("📊 Current State Analysis:")
    print("\n🟢 Advantages:")
    for pro in current_state['pros']:
        print(f"   {pro}")
    
    print("\n🔴 Challenges:")
    for con in current_state['cons']:
        print(f"   {con}")
    
    print("\n⚠️  Risk Assessment:")
    for level, risks in risk_factors.items():
        print(f"\n{level} Risk:")
        for risk in risks:
            print(f"   - {risk}")
    
    print("\n🎯 Recommended Timeline:")
    for timeline, actions in recommendations.items():
        print(f"\n{timeline}:")
        for action in actions:
            print(f"   - {action}")
    
    print("\n💡 Strategic Decision:")
    print("   🔥 RECOMMENDED: Start with ClarificationFlowService extraction")
    print("   📅 Timeline: Next sprint (non-breaking changes)")
    print("   🎯 Goal: Reduce main file by ~300 lines (25% reduction)")
    print("   ⚡ Benefit: Much easier testing and maintenance")

if __name__ == "__main__":
    print("🚀 LegalRAG Refactoring Analysis")
    print("=" * 70)
    
    # Step 1: Analyze current structure
    structure = analyze_rag_engine_structure()
    
    # Step 2: Identify concerns
    concerns = identify_concerns()
    
    # Step 3: Suggest refactoring plan
    suggestions = suggest_refactoring_plan()
    
    # Step 4: Assess priority
    assess_refactoring_priority()
    
    print("\n🎯 CONCLUSION:")
    print("   ✅ Current system works well - no urgent need")
    print("   📈 Refactoring will improve long-term maintainability")
    print("   🔧 Start with clarification flow extraction")
    print("   ⏰ Incremental approach - no big-bang rewrite")
