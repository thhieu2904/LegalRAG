# Analytics Implementation Plan# 📋 Analytics & Reporting Implementation Plan

## Overview**Status:** Planning Phase

Kế hoạch triển khai hệ thống Analytics cho LegalRAG - theo dõi hiệu suất, hành vi người dùng, và chất lượng RAG responses.**Created:** October 22, 2025

**Owner:** LegalRAG Team

## Phase 1: Foundation (Week 1-2)**Duration Estimate:** 3-4 hours

- [ ] Setup Analytics Database (ClickHouse hoặc PostgreSQL)**Priority:** HIGH (Required for reporting requirements)

- [ ] Create Event Schema

- [ ] Implement Event Tracking in Frontend---

- [ ] Implement Event Tracking in RAG Service

## 📌 Executive Summary

## Phase 2: Dashboard (Week 3-4)

- [ ] Create Grafana Dashboard**Objective:** Enable analytics and reporting capabilities for session data by time periods (daily/weekly/monthly/yearly).

- [ ] Setup Alerting Rules

- [ ] Real-time Metrics Visualization**Current State:**

- [ ] Historical Data Analysis

- ✅ Session data persisted to JSON files

## Phase 3: AI Insights (Week 5-6)- ✅ Query history stored with timestamps

- [ ] Implement ML-based Anomaly Detection- ✅ Routing metadata includes collection and confidence data

- [ ] Auto-generate Performance Reports- ❌ No analytics API endpoints

- [ ] Recommendation Engine- ❌ No reporting service to aggregate data

- [ ] Cost Optimization Analysis- ❌ No time-based query filtering

## Key Metrics to Track**Deliverables:**

1. **User Engagement**

   - Daily Active Users (DAU)1. `SessionAnalyticsService` - Core analytics logic

   - Session Duration2. Analytics API endpoints (5 endpoints)

   - Query Frequency3. CSV/JSON export functionality

2. Test suite for analytics

3. **RAG Performance**5. Documentation and examples

   - Query Response Time

   - Confidence Scores---

   - Collection Hit Rate

## 📊 Data Inventory

3. **Business Metrics**

   - Feature Usage### Source Data Location

   - Error Rates

   - User Satisfaction```

/app/data/sessions/

## Architecture├── daily_counter.json # Counter: {"counter": 3, "date": "20251018", "last_saved": "..."}

````└── sessions/

Frontend → Analytics API → Analytics DB → Dashboard    ├── 20251018-001.json       # Session files with query history

         ↓    ├── 20251018-002.json

    RAG Service → Analytics API    └── 20251018-003.json

         ↓```

  Admin Service → Analytics API

```### Available Data in Session File



## Success Criteria```json

- [ ] 95% uptime for Analytics system{

- [ ] < 100ms latency for event ingestion  "session_id": "20251018-003",

- [ ] Real-time dashboard updates (< 5s delay)  "created_at": 1760810170.88,

- [ ] 12 months data retention  "last_accessed": 1760810181.14,

- [ ] Cost per event < $0.0001  "query_history": [

    {
      "query": "Ai là người ký giấy khai sinh được đăng ký lại?",
      "answer": "...",
      "timestamp": 1760810205.56,          // ← Unix timestamp (queryable)
      "nucleus_chunks_count": 1,
      "context_length": 1987
    }
  ],
  "metadata": {
    "original_routing_context": {
      "target_collection": "quy_trinh_cap_ho_tich_cap_xa",  // ← Collection
      "confidence": 0.6577,                // ← Quality metric
      "top_similar_questions": [...]
    }
  }
}
````

### Queryable Fields

- `session_id` (YYYYMMDD-XXX format)
- `created_at` (Unix timestamp)
- `query_history[].timestamp` (Unix timestamp)
- `query_history[].query` (text)
- `query_history[].answer` (text)
- `metadata.target_collection` (string)
- `metadata.confidence` (float 0-1)
- `query_history[].context_length` (int)

---

## 🎯 Deliverables Breakdown

### Deliverable 1: SessionAnalyticsService Class

**File:** `rag_service/app/services/session_analytics.py`

**Responsibilities:**

- Load all session files for date range
- Parse and validate session data
- Aggregate statistics by date/week/month/year
- Calculate quality metrics
- Export to JSON/CSV

**Key Methods:**

```python
class SessionAnalyticsService:
    """Analytics service for session data queries and reporting"""

    def __init__(self, persistence_manager: SessionPersistenceManager)

    # Core Query Methods
    def get_sessions_by_date(self, date: str) -> List[OptimizedChatSession]
    def get_sessions_by_date_range(self, start_date: str, end_date: str) -> List[OptimizedChatSession]
    def get_sessions_by_week(self, year: int, week: int) -> List[OptimizedChatSession]
    def get_sessions_by_month(self, year: int, month: int) -> List[OptimizedChatSession]
    def get_sessions_by_year(self, year: int) -> List[OptimizedChatSession]

    # Statistics Methods
    def get_daily_statistics(self, date: str) -> Dict
    def get_weekly_statistics(self, year: int, week: int) -> Dict
    def get_monthly_statistics(self, year: int, month: int) -> Dict
    def get_yearly_statistics(self, year: int) -> Dict
    def get_date_range_statistics(self, start_date: str, end_date: str) -> Dict

    # Collection Analytics
    def get_collection_usage(self, start_date: str, end_date: str) -> Dict
    def get_collection_statistics(self, start_date: str, end_date: str) -> Dict

    # Quality Metrics
    def get_quality_metrics(self, start_date: str, end_date: str) -> Dict
    def get_confidence_distribution(self, start_date: str, end_date: str) -> Dict

    # Export Methods
    def export_to_json(self, data: Dict, filepath: str) -> None
    def export_to_csv(self, data: Dict, filepath: str) -> None

    # Helper Methods
    def _load_session_file(self, filepath: str) -> Optional[OptimizedChatSession]
    def _get_sessions_for_date(self, date: str) -> List[OptimizedChatSession]
    def _date_to_unix_timestamp(self, date: str) -> Tuple[float, float]
    def _calculate_week(self, timestamp: float) -> int
    def _calculate_month(self, timestamp: float) -> int
    def _calculate_year(self, timestamp: float) -> int
```

**Implementation Details:**

| Method                     | Complexity | Time   | Notes                                       |
| -------------------------- | ---------- | ------ | ------------------------------------------- |
| get_sessions_by_date       | Low        | 5 min  | Load files matching YYYYMMDD-\* pattern     |
| get_sessions_by_date_range | Low        | 10 min | Iterate through date range, load all        |
| get_sessions_by_week       | Medium     | 15 min | Calculate ISO week from timestamp           |
| get_sessions_by_month      | Low        | 10 min | Filter by year-month                        |
| get_sessions_by_year       | Low        | 10 min | Filter by year                              |
| get_daily_statistics       | Low        | 10 min | Count sessions, sum queries, avg confidence |
| get_weekly_statistics      | Medium     | 15 min | Aggregate daily stats for week              |
| get_monthly_statistics     | Medium     | 15 min | Aggregate daily stats for month             |
| get_yearly_statistics      | Medium     | 15 min | Aggregate monthly stats for year            |
| get_collection_usage       | Low        | 10 min | Count target_collection occurrences         |
| get_quality_metrics        | Low        | 10 min | Calculate avg/min/max confidence            |
| export_to_json             | Low        | 5 min  | Use json.dump()                             |
| export_to_csv              | Low        | 10 min | Use csv module with headers                 |

**Estimated Effort:** 1.5-2 hours

---

### Deliverable 2: Analytics API Endpoints

**File:** `rag_service/app/api/analytics.py` (NEW)

**Router:** `/api/v1/analytics`

**Endpoints:**

#### 2.1 GET /analytics/summary

```python
@router.get("/analytics/summary", tags=["analytics"])
async def get_summary() -> Dict:
    """
    Get overall analytics summary

    Returns:
        {
            "total_sessions": 287,
            "total_queries": 1245,
            "date_range": {
                "earliest": "2025-10-01",
                "latest": "2025-10-22"
            },
            "storage": {
                "total_size_kb": 45.3,
                "average_session_size_kb": 0.158
            }
        }
    """
```

**Implementation:**

```python
def __init__(self, analytics_service: SessionAnalyticsService):
    self.analytics = analytics_service

async def get_summary():
    stats = self.analytics.get_date_range_statistics("2025-10-01", datetime.now().strftime("%Y-%m-%d"))
    return {
        "total_sessions": len(all_sessions),
        "total_queries": sum(len(s.query_history) for s in all_sessions),
        "date_range": {...},
        "storage": {...}
    }
```

**Estimated Effort:** 10 minutes

---

#### 2.2 GET /analytics/sessions/daily/{date}

```python
@router.get("/analytics/sessions/daily/{date}", tags=["analytics"])
async def get_daily_analytics(date: str) -> Dict:
    """
    Get analytics for a specific date (YYYYMMDD format)

    Example: /analytics/sessions/daily/20251022

    Returns:
        {
            "date": "2025-10-22",
            "sessions": {
                "total": 5,
                "created": 2,
                "with_queries": 4
            },
            "queries": {
                "total": 12,
                "average_per_session": 2.4
            },
            "confidence": {
                "average": 0.71,
                "min": 0.45,
                "max": 0.95
            },
            "collections": {
                "quy_trinh_cap_ho_tich_cap_xa": 7,
                "quy_trinh_luat_su": 3,
                "other": 2
            }
        }
    """
```

**Implementation:**

```python
async def get_daily_analytics(date: str):
    validate_date_format(date)  # YYYYMMDD
    sessions = self.analytics.get_sessions_by_date(date)
    return self.analytics.get_daily_statistics(date)
```

**Estimated Effort:** 15 minutes

---

#### 2.3 GET /analytics/sessions/monthly/{year_month}

```python
@router.get("/analytics/sessions/monthly/{year_month}", tags=["analytics"])
async def get_monthly_analytics(year_month: str) -> Dict:
    """
    Get analytics for a specific month (YYYYMM format)

    Example: /analytics/sessions/monthly/202510

    Returns:
        {
            "period": "2025-10",
            "month": "October",
            "sessions": {
                "total": 287,
                "daily_average": 9.3
            },
            "queries": {
                "total": 1245,
                "daily_average": 40.2
            },
            "confidence": {
                "average": 0.71,
                "trend": "stable"
            },
            "collections": {
                "quy_trinh_cap_ho_tich_cap_xa": 425,
                "quy_trinh_luat_su": 185,
                ...
            },
            "peak_day": {
                "date": "2025-10-18",
                "queries": 98
            }
        }
    """
```

**Implementation:**

```python
async def get_monthly_analytics(year_month: str):
    validate_month_format(year_month)  # YYYYMM
    year, month = parse_year_month(year_month)
    sessions = self.analytics.get_sessions_by_month(year, month)
    return self.analytics.get_monthly_statistics(year, month)
```

**Estimated Effort:** 20 minutes

---

#### 2.4 GET /analytics/sessions/yearly/{year}

```python
@router.get("/analytics/sessions/yearly/{year}", tags=["analytics"])
async def get_yearly_analytics(year: str) -> Dict:
    """
    Get analytics for a specific year (YYYY format)

    Example: /analytics/sessions/yearly/2025

    Returns:
        {
            "year": 2025,
            "sessions": {
                "total": 2341,
                "monthly_average": 195
            },
            "queries": {
                "total": 9876,
                "monthly_average": 823
            },
            "confidence": {
                "average": 0.68,
                "trend": "declining"
            },
            "collections": {
                "quy_trinh_cap_ho_tich_cap_xa": 3456,
                ...
            },
            "peak_month": {
                "month": "October",
                "queries": 1245
            }
        }
    """
```

**Implementation:**

```python
async def get_yearly_analytics(year: str):
    validate_year_format(year)  # YYYY
    sessions = self.analytics.get_sessions_by_year(int(year))
    return self.analytics.get_yearly_statistics(int(year))
```

**Estimated Effort:** 20 minutes

---

#### 2.5 GET /analytics/export

```python
@router.get("/analytics/export", tags=["analytics"])
async def export_analytics(
    date_from: str = Query(..., description="Start date (YYYYMMDD)"),
    date_to: str = Query(..., description="End date (YYYYMMDD)"),
    format: str = Query("json", regex="^(json|csv)$")
) -> Union[Dict, FileResponse]:
    """
    Export analytics data for date range

    Example: /analytics/export?date_from=20251001&date_to=20251031&format=csv

    Returns:
        - JSON: Raw statistics data
        - CSV: Downloadable CSV file with daily breakdown
    """
```

**Implementation:**

```python
async def export_analytics(date_from: str, date_to: str, format: str = "json"):
    validate_date_format(date_from)
    validate_date_format(date_to)

    stats = self.analytics.get_date_range_statistics(date_from, date_to)

    if format == "json":
        return stats
    elif format == "csv":
        csv_path = self.analytics.export_to_csv(stats, "/tmp/analytics.csv")
        return FileResponse(csv_path, filename="analytics.csv")
```

**Estimated Effort:** 25 minutes

---

**Total Endpoints Effort:** ~90 minutes (1.5 hours)

---

### Deliverable 3: Integration into Main App

**File:** `rag_service/main.py`

**Changes:**

```python
# Add import
from app.api import analytics as analytics_router
from app.services.session_analytics import SessionAnalyticsService

# In app initialization
# 1. Initialize analytics service
analytics_service = SessionAnalyticsService(
    persistence_manager=session_persistence_manager
)

# 2. Register analytics router
app.include_router(
    analytics_router.router,
    prefix="/api/v1",
    tags=["analytics"]
)
```

**Estimated Effort:** 5 minutes

---

### Deliverable 4: Unit Tests

**File:** `rag_service/tests/test_analytics.py`

**Test Cases:**

| Test Name                        | Type        | Effort |
| -------------------------------- | ----------- | ------ |
| test_load_sessions_by_date       | Unit        | 5 min  |
| test_load_sessions_by_date_range | Unit        | 5 min  |
| test_get_daily_statistics        | Unit        | 10 min |
| test_get_monthly_statistics      | Unit        | 10 min |
| test_get_yearly_statistics       | Unit        | 10 min |
| test_get_collection_usage        | Unit        | 5 min  |
| test_get_quality_metrics         | Unit        | 5 min  |
| test_export_to_json              | Unit        | 5 min  |
| test_export_to_csv               | Unit        | 5 min  |
| test_api_daily_endpoint          | Integration | 10 min |
| test_api_monthly_endpoint        | Integration | 10 min |
| test_api_yearly_endpoint         | Integration | 10 min |
| test_api_export_endpoint         | Integration | 10 min |

**Total Test Effort:** ~95 minutes (1.5-2 hours)

---

### Deliverable 5: Documentation

**Files to Create:**

1. **ANALYTICS_API_DOCUMENTATION.md**

   - API endpoint reference
   - Request/response examples
   - Error codes
   - Rate limiting
   - Estimated effort: 30 minutes

2. **ANALYTICS_USAGE_EXAMPLES.md**

   - Python examples
   - cURL examples
   - React/frontend examples
   - Estimated effort: 20 minutes

3. **ANALYTICS_TROUBLESHOOTING.md**
   - Common issues
   - Debug tips
   - Performance optimization
   - Estimated effort: 15 minutes

**Total Documentation Effort:** ~65 minutes (1 hour)

---

## 🏗️ Implementation Timeline

### Phase 1: Core Service (1.5-2 hours)

```
Day 1 - Morning:
├─ Create session_analytics.py
├─ Implement data loading methods
├─ Implement statistics calculation
└─ Implement export methods
```

**Files Changed/Created:**

- ✅ `rag_service/app/services/session_analytics.py` (NEW - 400-500 lines)

**Time Estimate:** 1.5-2 hours

---

### Phase 2: API Endpoints (1.5 hours)

```
Day 1 - Afternoon:
├─ Create analytics.py router
├─ Implement 5 endpoints
├─ Add validation and error handling
└─ Integrate into main.py
```

**Files Changed/Created:**

- ✅ `rag_service/app/api/analytics.py` (NEW - 200-250 lines)
- ✏️ `rag_service/main.py` (MODIFIED - 5 lines added)

**Time Estimate:** 1.5 hours

---

### Phase 3: Testing & Validation (1-1.5 hours)

```
Day 2 - Morning:
├─ Create test suite
├─ Test with sample data
├─ Verify all endpoints
└─ Test export functionality
```

**Files Changed/Created:**

- ✅ `rag_service/tests/test_analytics.py` (NEW - 300-400 lines)

**Time Estimate:** 1-1.5 hours

**Docker Build & Test:**

```bash
# Rebuild image
docker-compose -f docker-compose.dev.yml build rag-service

# Start services
docker-compose -f docker-compose.dev.yml up

# Test endpoints
curl http://localhost:8000/api/v1/analytics/summary
curl http://localhost:8000/api/v1/analytics/sessions/daily/20251022
```

---

### Phase 4: Documentation (1 hour)

```
Day 2 - Afternoon:
├─ API documentation
├─ Usage examples
├─ Troubleshooting guide
└─ Commit and push
```

**Files Changed/Created:**

- ✅ `docs/ANALYTICS_API_DOCUMENTATION.md` (NEW - 300-400 lines)
- ✅ `docs/ANALYTICS_USAGE_EXAMPLES.md` (NEW - 200-300 lines)
- ✅ `docs/ANALYTICS_TROUBLESHOOTING.md` (NEW - 150-200 lines)

**Time Estimate:** 1 hour

---

## 📈 Total Effort Estimate

| Phase                  | Effort        | Status  |
| ---------------------- | ------------- | ------- |
| Service Implementation | 1.5-2h        | 🔄 TODO |
| API Endpoints          | 1.5h          | 🔄 TODO |
| Testing & Validation   | 1-1.5h        | 🔄 TODO |
| Documentation          | 1h            | 🔄 TODO |
| **TOTAL**              | **5-6 hours** | 🔄 TODO |

**Timeline:** 1-2 days (2-3 hours per day, realistic)

---

## 🎯 Success Criteria

### Before Implementation

- [ ] Analyze current session data structure
- [ ] Design analytics service and API endpoints
- [ ] Approve implementation plan

### After Implementation

- [ ] SessionAnalyticsService class created
- [ ] All 5 API endpoints working
- [ ] CSV/JSON export functional
- [ ] All unit tests passing
- [ ] Documentation complete
- [ ] Docker image rebuilt and tested
- [ ] Sample reports generated
- [ ] Endpoints tested with curl/Postman

---

## 📋 Checklist

### Preparation (Before Starting)

- [ ] Review ANALYTICS_AND_REPORTING_ANALYSIS.md
- [ ] Understand data structure in session files
- [ ] Verify docker-compose.dev.yml is running
- [ ] Have test session data available

### Implementation Phase 1: Service

- [ ] Create `rag_service/app/services/session_analytics.py`
- [ ] Implement data loading methods
- [ ] Implement statistics calculation
- [ ] Implement export methods
- [ ] Handle edge cases (empty data, invalid dates)
- [ ] Add logging

### Implementation Phase 2: API

- [ ] Create `rag_service/app/api/analytics.py`
- [ ] Implement /summary endpoint
- [ ] Implement /sessions/daily/{date} endpoint
- [ ] Implement /sessions/monthly/{year_month} endpoint
- [ ] Implement /sessions/yearly/{year} endpoint
- [ ] Implement /export endpoint
- [ ] Add error handling and validation
- [ ] Update main.py to include router

### Testing Phase

- [ ] Create test file with all test cases
- [ ] Test data loading from files
- [ ] Test statistics calculation accuracy
- [ ] Test API endpoints with sample data
- [ ] Test export to JSON and CSV
- [ ] Test error handling (invalid dates, missing data)
- [ ] Run all tests and verify passing

### Documentation Phase

- [ ] Create API documentation
- [ ] Add usage examples (Python, cURL, React)
- [ ] Create troubleshooting guide
- [ ] Add to main README

### Deployment Phase

- [ ] Rebuild Docker image
- [ ] Test with live container
- [ ] Verify endpoints accessible
- [ ] Generate sample reports
- [ ] Commit changes to git
- [ ] Push to repository

---

## 🚀 Quick Start Command

Once implemented, you'll be able to:

```bash
# Get today's report
curl "http://localhost:8000/api/v1/analytics/sessions/daily/20251022"

# Get October 2025 report
curl "http://localhost:8000/api/v1/analytics/sessions/monthly/202510"

# Get 2025 report
curl "http://localhost:8000/api/v1/analytics/sessions/yearly/2025"

# Export October to CSV
curl "http://localhost:8000/api/v1/analytics/export?date_from=20251001&date_to=20251031&format=csv" \
  -o report_oct_2025.csv

# Get overall summary
curl "http://localhost:8000/api/v1/analytics/summary"
```

---

## 📚 Related Documents

- [x] ANALYTICS_AND_REPORTING_ANALYSIS.md - Analysis complete
- [ ] ANALYTICS_API_DOCUMENTATION.md - To be created
- [ ] ANALYTICS_USAGE_EXAMPLES.md - To be created
- [ ] ANALYTICS_TROUBLESHOOTING.md - To be created
- [x] SESSION_PERSISTENCE_ANALYSIS.md - Persistence complete

---

## 💬 Notes

### Design Decisions

**Why not use a database?**

- ✅ JSON files sufficient for current scale (<10K sessions/day)
- ✅ No additional infrastructure (DB server)
- ✅ Easy to backup and migrate
- ✅ Can add Redis/SQL later if needed

**Why separate analytics service?**

- ✅ Single responsibility principle
- ✅ Easy to test independently
- ✅ Can be scaled separately if needed
- ✅ Reusable across multiple endpoints

**Why these 5 endpoints?**

- ✅ Cover all common reporting needs (daily/weekly/monthly/yearly)
- ✅ Summary for quick overview
- ✅ Export for external tools (Excel, Tableau)
- ✅ Extensible for future endpoints

### Future Enhancements

- Add weekly endpoint (/sessions/weekly/{year_week})
- Add custom date range queries
- Add filtering by collection
- Add confidence threshold filtering
- Add automated daily/weekly reports via email
- Add charts/visualization on admin dashboard
- Add caching for frequently accessed reports

---

**Status:** Ready for Implementation  
**Approval Required:** YES  
**Approved By:** [Pending]  
**Approval Date:** [TBD]

---

_Plan created: October 22, 2025_  
_Last updated: October 22, 2025_
