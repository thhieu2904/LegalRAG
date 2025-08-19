# Clarification System Fix - Embedding-Based Similarity

## Problem Analysis

### User's Original Issue

When users chose a collection in the clarification system (Step 2→3), the system was showing suggestions from the first procedures in the collection instead of relevant procedures related to the originally matched query.

**Example:**

- User query: "làm sao để khai tử người thân" (death registration)
- System showed: "01. Đăng ký khai sinh.json" (birth registration) instead of "15. Đăng ký khai tử.json" (death registration)

### Root Cause

In the `handle_clarification` method (Step 2→3 transition), the system was using:

```python
example_questions = self.smart_router.get_example_questions_for_collection(collection)
```

This method returns **ALL** example questions from a collection, not the ones similar to the originally matched procedure.

## Solution Implementation

### 1. New Smart Router Method

**File:** `backend/app/services/smart_router.py`

Added `get_similar_procedures_for_collection()` method that:

- Takes the original matched query/procedure as reference
- Uses embedding similarity to find the most relevant procedures in the selected collection
- Returns top-k similar procedures ranked by cosine similarity
- Includes fallback to original method if similarity search fails

```python
def get_similar_procedures_for_collection(
    self,
    collection_name: str,
    reference_query: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    # Uses SentenceTransformer embeddings and cosine similarity
    # Returns procedures with similarity scores
```

### 2. Enhanced Session Management

**File:** `backend/app/services/rag_engine.py`

Modified `_generate_smart_clarification()` to store routing context:

```python
# Store routing context in session for Step 2→3 similarity matching
session.metadata['original_routing_context'] = routing_result
session.metadata['original_query'] = query
```

### 3. Updated Step 2→3 Logic

**File:** `backend/app/services/rag_engine.py`

Modified `handle_clarification()` Step 2→3 transition to:

1. Retrieve original routing context from session
2. Use the originally matched procedure/query as reference
3. Call `get_similar_procedures_for_collection()` instead of `get_example_questions_for_collection()`
4. Return procedures ranked by embedding similarity

## Technical Details

### Embedding Similarity Process

1. **Reference Extraction**: Get original query or best matched procedure from routing context
2. **Embedding Generation**: Create embedding vector for reference query using SentenceTransformer
3. **Collection Search**: Get all example questions in selected collection
4. **Similarity Calculation**: Compute cosine similarity between reference and each collection procedure
5. **Ranking**: Sort by similarity score and return top-k results
6. **Diversity**: Avoid duplicate procedures from same source document

### Fallback Strategy

- If no routing context available → Use original method
- If no similar procedures found → Use original method
- If similarity search fails → Use original method

### Debug Information

Added debug fields to clarification response:

```json
{
  "clarification": {
    "similarity_used": true,
    "options": [
      {
        "similarity": 0.85,
        "title": "Relevant procedure...",
        ...
      }
    ]
  }
}
```

## Testing Results

### Test Case: Death Registration Query

**Input:** "làm sao để khai tử người thân"

**Before Fix:**

- Showed: "01. Đăng ký khai sinh.json" (birth registration)
- Relevance: ❌ Irrelevant

**After Fix:**

- Shows: "15. Đăng ký khai tử.json" (death registration)
- Similarity: 1.000 (100% match)
- Relevance: ✅ Highly relevant

## Benefits

1. **Higher Relevance**: Users see procedures actually related to their original query
2. **Better UX**: More intuitive clarification suggestions that make sense
3. **Maintains Performance**: Fast embedding similarity search with caching
4. **Robust Fallbacks**: System still works if similarity search fails
5. **Debug Support**: Similarity scores help track system performance

## Files Modified

1. **backend/app/services/smart_router.py**

   - Added `get_similar_procedures_for_collection()` method
   - Embedding-based similarity search implementation

2. **backend/app/services/rag_engine.py**

   - Enhanced session metadata storage in `_generate_smart_clarification()`
   - Updated Step 2→3 logic in `handle_clarification()` to use similarity search

3. **Test Files Added**
   - `test_similarity_method.py` - Validates similarity method with mock data
   - `test_clarification_fix.py` - Full integration test (requires environment)

## Impact

This fix resolves the core issue in the multi-turn clarification system where users were getting irrelevant procedure suggestions. The system now intelligently matches user queries to the most similar procedures using state-of-the-art embedding similarity, significantly improving the user experience and system accuracy.

## Future Enhancements

1. **Similarity Threshold**: Add minimum similarity threshold to filter out weak matches
2. **Category Weighting**: Give higher weights to procedures in same category as original match
3. **Temporal Relevance**: Consider recency/frequency of procedure usage
4. **User Feedback**: Learn from user selections to improve similarity matching
5. **Multi-language Support**: Extend similarity matching to other languages

## Monitoring

Key metrics to monitor:

- `similarity_used` flag in clarification responses
- User selection patterns after similarity-based suggestions
- Average similarity scores of selected procedures
- Fallback usage frequency (indicates embedding model performance)
