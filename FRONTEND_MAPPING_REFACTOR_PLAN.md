# 🏗️ REFACTORING PLAN: MOVE MAPPING TO FRONTEND

## 📋 Current Problem Analysis

### Backend đang làm quá nhiều việc:

```python
# ❌ Backend hiện tại - WRONG APPROACH
{
  "collections": [
    {
      "name": "ho_tich_cap_xa",           # Frontend mapping
      "full_name": "quy_trinh_cap_ho_tich_cap_xa",  # Backend internal
      "title": "Hộ tịch cấp xã",          # UI display
      "description": "Thủ tục khai sinh..." # UI description
    }
  ]
}
```

### Frontend chỉ nhận passive data:

```tsx
// ❌ Frontend hiện tại - PASSIVE
const collections = await fetchCollections(); // Nhận fixed data
```

## 🎯 Target Architecture

### Backend: Pure Business Logic

```python
# ✅ Backend mới - CLEAN APPROACH
{
  "collections": [
    {
      "id": "quy_trinh_cap_ho_tich_cap_xa",
      "document_count": 53,
      "last_updated": "2024-08-23",
      "status": "active"
    }
  ]
}
```

### Frontend: Smart Presentation Layer

```tsx
// ✅ Frontend mới - INTELLIGENT
const collections = await fetchCollections();
const mappedCollections = collectionMapper.mapForDisplay(collections);
// Frontend tự quyết định hiển thị như thế nào
```

## 📅 Implementation Phases

### Phase 1: Backend Simplification (Week 1)

- [ ] Simplify API responses - chỉ trả business data
- [ ] Remove all display logic từ backend
- [ ] Keep compatibility layer tạm thời

### Phase 2: Frontend Mapping Service (Week 1-2)

- [ ] Create CollectionMappingService
- [ ] Implement mapping configuration
- [ ] Add admin interface để edit mappings

### Phase 3: Migration & Testing (Week 2)

- [ ] Gradually migrate components
- [ ] A/B test old vs new approach
- [ ] Performance testing

### Phase 4: Cleanup (Week 3)

- [ ] Remove compatibility layer
- [ ] Clean up backend code
- [ ] Documentation update

## 🔧 Detailed Implementation

### 1. Backend API Simplification

#### Current (Complex):

```python
@router.get("/collections")
async def get_collections():
    return {
        "collections": [
            {
                "name": "ho_tich_cap_xa",
                "full_name": "quy_trinh_cap_ho_tich_cap_xa",
                "title": "Hộ tịch cấp xã",
                "description": "Thủ tục khai sinh, kết hôn...",
                "file_count": 53
            }
        ]
    }
```

#### Target (Simple):

```python
@router.get("/collections")
async def get_collections():
    return {
        "collections": [
            {
                "id": "quy_trinh_cap_ho_tich_cap_xa",
                "document_count": 53,
                "question_count": 749,
                "last_updated": "2024-08-23T10:30:00Z",
                "status": "active",
                "metadata": {
                    "created_date": "2024-01-01",
                    "data_version": "1.0"
                }
            }
        ]
    }
```

### 2. Frontend Mapping Service

#### Collection Mapping Config:

```typescript
// src/config/collectionMappings.ts
export const collectionMappings = {
  quy_trinh_cap_ho_tich_cap_xa: {
    displayName: "Hộ tịch cấp xã",
    shortName: "ho_tich_cap_xa",
    description: "Thủ tục khai sinh, kết hôn, khai tử",
    icon: "🏛️",
    category: "dich_vu_hanh_chinh",
    keywords: ["khai sinh", "kết hôn", "khai tử"],
    color: "#3B82F6",
  },
  quy_trinh_chung_thuc: {
    displayName: "Chứng thực",
    shortName: "chung_thuc",
    description: "Chứng thực hợp đồng, chữ ký, bản sao",
    icon: "📋",
    category: "phap_ly",
    keywords: ["chứng thực", "hợp đồng", "chữ ký"],
    color: "#10B981",
  },
};
```

#### Mapping Service:

```typescript
// src/services/CollectionMappingService.ts
class CollectionMappingService {
  private mappings = collectionMappings;

  // Map backend data to frontend display
  mapCollectionForDisplay(backendCollection: BackendCollection) {
    const mapping = this.mappings[backendCollection.id];
    return {
      id: backendCollection.id,
      displayName:
        mapping?.displayName || this.generateDisplayName(backendCollection.id),
      shortName: mapping?.shortName || backendCollection.id,
      description: mapping?.description || "Không có mô tả",
      icon: mapping?.icon || "📄",
      documentCount: backendCollection.document_count,
      questionCount: backendCollection.question_count,
      ...mapping,
    };
  }

  // Generate display name từ ID nếu không có mapping
  private generateDisplayName(id: string): string {
    return id
      .replace(/quy_trinh_|thu_tuc_/g, "")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (l) => l.toUpperCase());
  }

  // Admin functions
  updateMapping(collectionId: string, mapping: CollectionMapping) {
    this.mappings[collectionId] = mapping;
    this.saveToStorage();
  }

  private saveToStorage() {
    localStorage.setItem("collection_mappings", JSON.stringify(this.mappings));
  }
}
```

### 3. Admin Interface

#### Admin Collection Manager:

```tsx
// src/components/admin/CollectionManager.tsx
const CollectionManager = () => {
  const [collections, setCollections] = useState([]);
  const [mappings, setMappings] = useState({});

  const updateMapping = (
    collectionId: string,
    newMapping: CollectionMapping
  ) => {
    // Update in-memory
    setMappings((prev) => ({ ...prev, [collectionId]: newMapping }));

    // Save to service
    collectionMappingService.updateMapping(collectionId, newMapping);

    // Optional: Sync to backend for persistence
    syncMappingToBackend(collectionId, newMapping);
  };

  return (
    <div className="collection-manager">
      {collections.map((collection) => (
        <CollectionMappingEditor
          key={collection.id}
          collection={collection}
          mapping={mappings[collection.id]}
          onUpdate={updateMapping}
        />
      ))}
    </div>
  );
};
```

## 🎖️ Benefits của approach này:

### 1. **Separation of Concerns**

- Backend: Pure business logic
- Frontend: Presentation logic
- Clear responsibility boundaries

### 2. **Scalability**

- Thêm collection mới không cần sửa backend
- Frontend tự handle display logic
- Admin có thể customize hiển thị

### 3. **Maintainability**

- Backend code đơn giản hơn
- Frontend mapping dễ test
- Clear data flow

### 4. **Flexibility**

- Multiple display modes (admin, user, mobile)
- Internationalization dễ dàng
- A/B testing display variants

### 5. **Performance**

- Backend responses nhỏ hơn
- Frontend caching mapping config
- Reduced server load

## 🔍 Areas cần refactor trong hệ thống:

1. **Router Service** - Remove display logic
2. **Clarification Service** - Use raw collection IDs
3. **API Endpoints** - Simplify responses
4. **Frontend Components** - Add mapping layer
5. **Admin Interface** - Collection management

## 📝 Migration Strategy:

### Step 1: Dual Mode Support

- Backend support both old & new format
- Frontend gradually adopt new approach
- No breaking changes initially

### Step 2: Component-by-component Migration

- Start with less critical components
- Test thoroughly
- Rollback capability

### Step 3: Full Migration

- Remove old format support
- Clean up backend code
- Performance optimization

Approach này sẽ giúp hệ thống trở nên scalable và maintainable hơn rất nhiều!
