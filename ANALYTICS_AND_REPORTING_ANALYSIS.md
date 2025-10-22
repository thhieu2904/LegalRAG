# 📊 Session Analytics & Reporting Analysis

**Question:** Hiện tại sẽ được hiển thị như nào? Có thể làm report theo tuần/tháng/năm không?

**Answer:** ✅ Data đã lưu đủ! Nhưng cần thêm analytics API. Mình show chi tiết:

---

## 📁 Dữ Liệu Hiện Tại Lưu Gì

### Session File: `20251018-003.json`

```json
{
  "session_id": "20251018-003",              // ← Có timestamp trong ID (YYYYMMDD)
  "created_at": 1760810170.88,              // ← Unix timestamp (epoch)
  "last_accessed": 1760810181.14,           // ← Unix timestamp

  "query_history": [
    {
      "query": "...",
      "answer": "...",
      "timestamp": 1760810205.56,           // ← Mỗi query có timestamp!
      "nucleus_chunks_count": 1,
      "context_length": 1987
    }
  ],

  "metadata": {
    "original_routing_context": {
      "target_collection": "quy_trinh_cap_ho_tich_cap_xa",  // ← Collection
      "confidence": 0.6577,                 // ← Confidence score
      "top_similar_questions": [...]        // ← Related questions
    }
  }
}
```

---

## 🔍 Hiện Tại Có Thể Query Được Gì?

### ✅ **CÓ THỂ TRỰC TIẾP:**

| Data             | Nằm Ở                            | Có thể query?          |
| ---------------- | -------------------------------- | ---------------------- |
| Session ID       | Filename: `20251018-003.json`    | ✅ Có (từ tên file)    |
| Date created     | `created_at`: 1760810170.88      | ✅ Có (unix timestamp) |
| Total queries    | `len(query_history)`             | ✅ Có (count array)    |
| Query text       | `query_history[].query`          | ✅ Có                  |
| Answer text      | `query_history[].answer`         | ✅ Có                  |
| Query timestamp  | `query_history[].timestamp`      | ✅ Có (unix timestamp) |
| Collection used  | `metadata.target_collection`     | ✅ Có                  |
| Confidence score | `metadata.confidence`            | ✅ Có                  |
| Context length   | `query_history[].context_length` | ✅ Có                  |

### ❌ **KHÔNG TRỰC TIẾP (cần calculate):**

| Report Type                  | Cần Làm Gì                                             |
| ---------------------------- | ------------------------------------------------------ |
| **Queries per day**          | Count queries by date from `query_history[].timestamp` |
| **Queries per week**         | Group by ISO week from `query_history[].timestamp`     |
| **Queries per month**        | Group by year-month from `query_history[].timestamp`   |
| **Average response quality** | Avg `metadata.confidence` scores                       |
| **Popular collections**      | Count by `metadata.target_collection`                  |
| **Most asked questions**     | Group by `query_history[].query`                       |
| **Active sessions**          | Count sessions by date range                           |

---

## 🔨 Cần Thêm Cái Gì Để Làm Report?

### Option 1: Add API Endpoints (Recommended)

**Thêm các endpoint này:**

```
GET /api/v1/analytics/sessions/summary
  └─ Trả: total sessions, total queries, date range

GET /api/v1/analytics/sessions/by-date?date=20251018
  └─ Trả: sessions được tạo on this date

GET /api/v1/analytics/sessions/by-week?week=2025-42
  └─ Trả: sessions created in week 42 of 2025

GET /api/v1/analytics/sessions/by-month?month=202510
  └─ Trả: sessions created in Oct 2025

GET /api/v1/analytics/sessions/by-year?year=2025
  └─ Trả: sessions created in 2025

GET /api/v1/analytics/queries/statistics
  └─ Trả: total queries, avg length, avg confidence

GET /api/v1/analytics/collections/usage
  └─ Trả: which collections used most

GET /api/v1/analytics/export?format=csv&date_from=20251001&date_to=20251031
  └─ Trả: export data as CSV/JSON for report
```

### Option 2: Add Analytics Service

**Create `session_analytics.py`:**

```python
class SessionAnalyticsService:
    def __init__(self, persistence_manager):
        self.persistence = persistence_manager

    def get_queries_by_date(self, date_str: str):
        """Get all queries for a specific date (YYYYMMDD)"""
        # Load all session files for that date
        # Parse query_history
        # Return list of queries

    def get_queries_by_week(self, year: int, week: int):
        """Get all queries for a specific week"""

    def get_queries_by_month(self, year: int, month: int):
        """Get all queries for a specific month"""

    def get_queries_by_year(self, year: int):
        """Get all queries for a specific year"""

    def get_collection_statistics(self, date_from, date_to):
        """Which collections are used most"""

    def export_to_csv(self, date_from, date_to):
        """Export sessions data to CSV"""
```

---

## 📊 Report Examples - What You Can See

### Example 1: Daily Report

```
Date: 2025-10-18
├─ Total Sessions: 3
├─ Total Queries: 5
├─ Average Confidence: 0.68
├─ Popular Collections:
│  ├─ quy_trinh_cap_ho_tich_cap_xa: 3 queries
│  └─ other_collection: 2 queries
└─ Top Questions:
   ├─ "Ai là người ký giấy khai sinh được đăng ký lại?" (1 time)
   └─ ...
```

### Example 2: Weekly Report

```
Week 42 of 2025 (Oct 13-19)
├─ Total Sessions: 42
├─ Total Queries: 156
├─ Daily Average: 22 queries/day
├─ Collections:
│  ├─ quy_trinh_cap_ho_tich_cap_xa: 45 queries (28.8%)
│  ├─ quy_trinh_luat_su: 32 queries (20.5%)
│  └─ ...
├─ Average Confidence: 0.72
└─ Response Quality: GOOD
```

### Example 3: Monthly Report

```
October 2025
├─ Total Sessions: 287
├─ Total Queries: 1,245
├─ Daily Average: 40.2 queries/day
├─ Peak Day: Oct 18 (98 queries)
├─ Collections:
│  ├─ quy_trinh_cap_ho_tich_cap_xa: 425 queries (34.1%)
│  ├─ quy_trinh_luat_su: 185 queries (14.8%)
│  └─ ...
├─ Average Confidence: 0.71
├─ Trend: ↑ 15% vs September
└─ Top Question: "Làm thế nào để..."
```

### Example 4: Yearly Report

```
Year 2025
├─ Total Sessions: 2,341
├─ Total Queries: 9,876
├─ Daily Average: 27.1 queries/day
├─ Peak Month: October (1,245 queries)
├─ Top Collections:
│  ├─ quy_trinh_cap_ho_tich_cap_xa: 3,456 queries (35%)
│  ├─ quy_trinh_luat_su: 1,854 queries (18.8%)
│  └─ ...
├─ Average Confidence: 0.68
├─ System Health: 92% uptime
└─ Insights: Stable usage pattern
```

---

## 🛠️ Implementation Path

### Step 1: Implement Analytics Service (Mình làm)

```python
# rag_service/app/services/session_analytics.py
class SessionAnalyticsService:
    def load_all_sessions_for_date(self, date):
        """Load all session files for a date"""

    def query_by_date_range(self, start_date, end_date):
        """Query sessions in date range"""

    def get_statistics(self, date_from, date_to):
        """Calculate statistics"""

    def export_to_json(self, data):
        """Export as JSON"""

    def export_to_csv(self, data):
        """Export as CSV"""
```

### Step 2: Add Analytics API Endpoints

```python
# rag_service/app/api/analytics.py
@router.get("/analytics/sessions/summary")
async def get_sessions_summary():
    """Get overall sessions summary"""

@router.get("/analytics/sessions/by-date/{date}")
async def get_sessions_by_date(date: str):
    """Get sessions for specific date"""

@router.get("/analytics/sessions/by-month/{year_month}")
async def get_sessions_by_month(year_month: str):
    """Get sessions for specific month"""

@router.get("/analytics/queries/statistics")
async def get_query_statistics(date_from, date_to):
    """Get query statistics"""

@router.get("/analytics/export")
async def export_data(date_from, date_to, format: str = "json"):
    """Export data for reporting"""
```

### Step 3: Update main.py

```python
# Include analytics router
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
```

---

## 🎯 What Data You Can Extract

### Timeline-Based Queries

```python
# Example: Get all queries from Oct 2025
analytics.query_by_date_range(
    start_date="2025-10-01",
    end_date="2025-10-31"
)

# Result:
# {
#   "total_sessions": 287,
#   "total_queries": 1245,
#   "by_date": {
#     "2025-10-01": {"sessions": 9, "queries": 42},
#     "2025-10-02": {"sessions": 12, "queries": 58},
#     ...
#   },
#   "by_collection": {...},
#   "by_hour": {...}
# }
```

### Collection Analytics

```python
# Get which collections are queried most
analytics.get_collection_usage(
    date_from="2025-10-01",
    date_to="2025-10-31"
)

# Result:
# {
#   "quy_trinh_cap_ho_tich_cap_xa": 425,
#   "quy_trinh_luat_su": 185,
#   ...
# }
```

### Quality Analytics

```python
# Get average confidence scores
analytics.get_quality_metrics(
    date_from="2025-10-01",
    date_to="2025-10-31"
)

# Result:
# {
#   "avg_confidence": 0.71,
#   "high_confidence_queries": 892,
#   "low_confidence_queries": 124,
#   "confidence_trend": "stable"
# }
```

---

## 📥 Export Format Examples

### JSON Export

```json
{
  "report_period": "2025-10-01 to 2025-10-31",
  "summary": {
    "total_sessions": 287,
    "total_queries": 1245,
    "avg_queries_per_session": 4.3
  },
  "daily_data": [
    {
      "date": "2025-10-01",
      "sessions": 9,
      "queries": 42,
      "avg_confidence": 0.68
    },
    ...
  ],
  "collection_breakdown": {
    "quy_trinh_cap_ho_tich_cap_xa": 425,
    ...
  }
}
```

### CSV Export

```csv
date,sessions,queries,avg_confidence,top_collection
2025-10-01,9,42,0.68,quy_trinh_cap_ho_tich_cap_xa
2025-10-02,12,58,0.71,quy_trinh_cap_ho_tich_cap_xa
2025-10-03,8,35,0.65,quy_trinh_luat_su
...
```

---

## ⚡ Quick Wins (Easy to Add)

### 1. Simple Daily Summary Endpoint (10 mins)

```python
@router.get("/analytics/daily/{date}")
async def get_daily_summary(date: str):
    """Get summary for one day"""
    # Load all {date}-*.json files
    # Count queries
    # Calculate metrics
    # Return summary
```

### 2. Collection Usage Endpoint (5 mins)

```python
@router.get("/analytics/collections")
async def get_collection_usage():
    """Most used collections"""
    # Scan all session files
    # Count by target_collection
    # Return sorted list
```

### 3. CSV Export Endpoint (15 mins)

```python
@router.get("/analytics/export/csv")
async def export_csv(date_from, date_to):
    """Export as CSV for Excel"""
    # Load sessions in range
    # Format as CSV
    # Return file download
```

---

## 📋 Decision: What to Implement First?

### Option A: Full Analytics Suite (2-3 hours)

✅ Weekly/monthly/yearly reports  
✅ Collection analytics  
✅ Quality metrics  
✅ CSV/JSON export  
✅ Charts ready (frontend can use)

**Recommended if:** You need comprehensive reporting

### Option B: Simple Daily/Monthly (1 hour)

✅ Daily summary endpoint  
✅ Monthly summary endpoint  
✅ Basic export to JSON

**Recommended if:** Quick solution needed

### Option C: DIY Query (0 hours)

✅ Can manually query JSON files  
✅ Write Python script to analyze  
✅ Use jq command to extract

**Recommended if:** Just for testing

---

## 🎯 My Recommendation

**Implement:** Option A (Full Analytics Suite)

**Why:**

1. Data already persisted (easy to query)
2. Endpoints take ~30 mins each
3. Future-proof for growth
4. Can generate reports automatically
5. Admin dashboard can use these endpoints

**Timeline:**

- Day 1: Implement analytics service (1 hour)
- Day 2: Add API endpoints (1 hour)
- Day 3: Test & verify (30 mins)

---

## 💡 Future Extensions

Once analytics API is ready:

1. **Automated Reports** - Send daily/weekly reports via email
2. **Charts & Visualizations** - Add charts to admin dashboard
3. **Anomaly Detection** - Alert if query count drops
4. **Trend Analysis** - Show improvement/degradation
5. **User Segmentation** - Analyze by collection/user
6. **Performance Alerts** - Alert if confidence drops below threshold

---

**Status:**

- ✅ Data structure: READY
- ❌ Analytics API: NOT YET
- ✅ Easy to add: YES

---

_Analysis: October 22, 2025_
