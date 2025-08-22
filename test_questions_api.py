#!/usr/bin/env python3
"""
Test script to verify router CRUD API endpoints
"""

import requests
import json
import sys
from datetime import datetime

API_BASE = "http://localhost:8000/router"

def test_get_collections():
    """Test GET /collections endpoint"""
    print("🔍 Testing GET /collections...")
    try:
        response = requests.get(f"{API_BASE}/collections")
        response.raise_for_status()
        
        collections = response.json()
        print(f"✅ Found {len(collections)} collections:")
        for col in collections:
            print(f"   📁 {col['display_name']} ({col['name']}) - {col['total_questions']} questions")
        
        return collections
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def test_get_collection_questions(collection_name):
    """Test GET /collections/{name}/questions endpoint"""
    print(f"\n🔍 Testing GET /collections/{collection_name}/questions...")
    try:
        response = requests.get(f"{API_BASE}/collections/{collection_name}/questions")
        response.raise_for_status()
        
        questions = response.json()
        print(f"✅ Found {len(questions)} questions in {collection_name}")
        
        if questions:
            sample = questions[0]
            print(f"   📝 Sample question: {sample.get('text', '')[:80]}...")
            print(f"   🏷️  Category: {sample.get('category', 'N/A')}")
            print(f"   🎯 Priority: {sample.get('priority_score', 0)}")
            print(f"   📊 Status: {sample.get('status', 'N/A')}")
        
        return questions
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def test_create_question(collection_name):
    """Test POST /collections/{name}/questions endpoint"""
    print(f"\n🔍 Testing POST /collections/{collection_name}/questions...")
    
    test_question = {
        "text": f"Test question created at {datetime.now().strftime('%H:%M:%S')}",
        "keywords": ["test", "api", "crud"],
        "category": "test_category",
        "type": "variant",
        "priority_score": 0.7
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/collections/{collection_name}/questions",
            json=test_question,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Question created successfully!")
        print(f"   📝 Question ID: {result.get('question_id', 'N/A')}")
        print(f"   📁 Collection: {result.get('collection', 'N/A')}")
        
        return result.get('question_id')
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_search_questions(query):
    """Test GET /search endpoint"""
    print(f"\n🔍 Testing GET /search?q={query}...")
    try:
        response = requests.get(f"{API_BASE}/search", params={"q": query, "limit": 5})
        response.raise_for_status()
        
        results = response.json()
        print(f"✅ Found {len(results)} search results:")
        for result in results:
            score = result.get('similarity_score', 0)
            text = result.get('text', '')[:60]
            print(f"   🎯 {score:.3f} - {text}...")
        
        return results
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def main():
    print("🚀 Testing Router CRUD API endpoints...")
    print("=" * 50)
    
    # Test 1: Get collections
    collections = test_get_collections()
    if not collections:
        print("❌ No collections found. Cannot proceed with tests.")
        sys.exit(1)
    
    # Use first collection for testing
    test_collection = collections[0]['name']
    print(f"\n📋 Using collection '{test_collection}' for testing...")
    
    # Test 2: Get questions in collection
    questions = test_get_collection_questions(test_collection)
    
    # Test 3: Create a new question
    question_id = test_create_question(test_collection)
    
    # Test 4: Search questions
    if questions:
        # Use keywords from first question for search
        first_question = questions[0]
        keywords = first_question.get('keywords', [])
        if keywords:
            test_search_questions(keywords[0])
        else:
            test_search_questions("thủ tục")
    
    print("\n" + "=" * 50)
    print("🎉 API testing completed!")
    
    if question_id:
        print(f"\n💡 Note: Created test question with ID '{question_id}'")
        print("   You may want to delete it manually from the admin interface.")

if __name__ == "__main__":
    main()
