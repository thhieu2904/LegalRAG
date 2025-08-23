/**
 * 🎨 SMART COLLECTION LIST COMPONENT
 *
 * Demonstrates how frontend handles mapping intelligently.
 * Backend provides business data, frontend handles ALL presentation.
 */

import React, { useState, useEffect } from "react";
import {
  collectionMappingService,
  type BackendCollection,
  type DisplayCollection,
  type CollectionMapping,
} from "../services/CollectionMappingService";

// API service to fetch business data from backend
class CollectionBusinessAPI {
  private baseURL = "http://localhost:8000/router";

  async fetchCollections(): Promise<BackendCollection[]> {
    const response = await fetch(`${this.baseURL}/collections`);
    const data = await response.json();
    return data.collections;
  }

  async fetchCollectionStats(collectionId: string) {
    const response = await fetch(
      `${this.baseURL}/collections/${collectionId}/stats`
    );
    return response.json();
  }
}

const collectionAPI = new CollectionBusinessAPI();

// Component Props
interface SmartCollectionListProps {
  viewMode?: "grid" | "list" | "category";
  showStats?: boolean;
  allowSearch?: boolean;
  adminMode?: boolean;
}

const SmartCollectionList: React.FC<SmartCollectionListProps> = ({
  viewMode: initialViewMode = "grid",
  showStats = false,
  allowSearch = true,
  adminMode = false,
}) => {
  // State
  const [backendCollections, setBackendCollections] = useState<
    BackendCollection[]
  >([]);
  const [displayCollections, setDisplayCollections] = useState<
    DisplayCollection[]
  >([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [viewMode, setViewMode] = useState(initialViewMode);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load data on mount
  useEffect(() => {
    loadCollections();
  }, []);

  // Map and filter collections when data changes
  useEffect(() => {
    if (backendCollections.length > 0) {
      let mapped =
        collectionMappingService.mapCollectionsForDisplay(backendCollections);

      // Apply search filter
      if (searchTerm) {
        mapped = collectionMappingService.searchCollections(
          backendCollections,
          searchTerm
        );
      }

      // Apply category filter
      if (selectedCategory !== "all") {
        mapped = mapped.filter((col) => col.category === selectedCategory);
      }

      setDisplayCollections(mapped);
    }
  }, [backendCollections, searchTerm, selectedCategory]);

  const loadCollections = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch business data from backend
      const businessData = await collectionAPI.fetchCollections();
      setBackendCollections(businessData);
    } catch (err) {
      setError("Failed to load collections");
      console.error("Error loading collections:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleMappingUpdate = (
    collectionId: string,
    newMapping: Partial<CollectionMapping>
  ) => {
    if (adminMode) {
      collectionMappingService.updateMapping(collectionId, newMapping);
      // Trigger re-render by updating display collections
      const updated =
        collectionMappingService.mapCollectionsForDisplay(backendCollections);
      setDisplayCollections(updated);
    }
  };

  // Get unique categories for filter
  const categories = [
    "all",
    ...new Set(displayCollections.map((col) => col.category)),
  ];

  // Render collection based on view mode
  const renderCollection = (collection: DisplayCollection) => {
    const categoryInfo = collectionMappingService.getCategoryInfo(
      collection.category
    );

    return (
      <div
        key={collection.id}
        className={`collection-card ${viewMode}`}
        style={{ borderLeft: `4px solid ${collection.color}` }}
      >
        <div className="collection-header">
          <span className="collection-icon" style={{ fontSize: "2rem" }}>
            {collection.icon}
          </span>
          <div className="collection-info">
            <h3 className="collection-title">{collection.displayName}</h3>
            <p className="collection-description">{collection.description}</p>
          </div>
          {adminMode && (
            <button
              className="edit-mapping-btn"
              onClick={() => handleMappingUpdate(collection.id, {})}
            >
              ✏️ Edit
            </button>
          )}
        </div>

        <div className="collection-meta">
          <span
            className="category-badge"
            style={{
              backgroundColor: categoryInfo.color + "20",
              color: categoryInfo.color,
            }}
          >
            {categoryInfo.icon} {categoryInfo.name}
          </span>
          <div className="collection-stats">
            <span>📄 {collection.documentCount} docs</span>
            <span>❓ {collection.questionCount} questions</span>
            <span className={`status ${collection.status}`}>
              {collection.status === "active" ? "✅" : "⭕"} {collection.status}
            </span>
          </div>
        </div>

        <div className="collection-keywords">
          {collection.keywords.slice(0, 3).map((keyword) => (
            <span key={keyword} className="keyword-tag">
              {keyword}
            </span>
          ))}
        </div>

        {showStats && (
          <div className="collection-detailed-stats">
            <small>Last updated: {collection.lastUpdated || "Unknown"}</small>
            <small>Priority: {collection.priority}</small>
          </div>
        )}
      </div>
    );
  };

  // Render by category
  const renderByCategory = () => {
    const grouped =
      collectionMappingService.getCollectionsByCategory(backendCollections);

    return (
      <div className="collections-by-category">
        {Object.entries(grouped).map(([categoryKey, collections]) => {
          const categoryInfo =
            collectionMappingService.getCategoryInfo(categoryKey);

          return (
            <div key={categoryKey} className="category-section">
              <h2 className="category-title">
                <span style={{ color: categoryInfo.color }}>
                  {categoryInfo.icon} {categoryInfo.name}
                </span>
                <span className="category-count">({collections.length})</span>
              </h2>
              <div className="category-collections">
                {collections.map(renderCollection)}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  if (loading) {
    return <div className="loading">Loading collections...</div>;
  }

  if (error) {
    return (
      <div className="error">
        <p>Error: {error}</p>
        <button onClick={loadCollections}>Retry</button>
      </div>
    );
  }

  return (
    <div className="smart-collection-list">
      {/* Header */}
      <div className="collection-list-header">
        <h1>Collections {adminMode && "(Admin Mode)"}</h1>
        <div className="collection-summary">
          {displayCollections.length} collections,{" "}
          {displayCollections.reduce((sum, col) => sum + col.questionCount, 0)}{" "}
          questions total
        </div>
      </div>

      {/* Controls */}
      <div className="collection-controls">
        {allowSearch && (
          <input
            type="text"
            placeholder="Search collections..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        )}

        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="category-filter"
        >
          {categories.map((category) => {
            const info =
              category === "all"
                ? { name: "All Categories" }
                : collectionMappingService.getCategoryInfo(category);
            return (
              <option key={category} value={category}>
                {info.name}
              </option>
            );
          })}
        </select>

        <div className="view-mode-buttons">
          <button
            className={viewMode === "grid" ? "active" : ""}
            onClick={() => setViewMode("grid")}
          >
            Grid
          </button>
          <button
            className={viewMode === "list" ? "active" : ""}
            onClick={() => setViewMode("list")}
          >
            List
          </button>
          <button
            className={viewMode === "category" ? "active" : ""}
            onClick={() => setViewMode("category")}
          >
            By Category
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="collection-content">
        {viewMode === "category" ? (
          renderByCategory()
        ) : (
          <div className={`collections-${viewMode}`}>
            {displayCollections.map(renderCollection)}
          </div>
        )}
      </div>

      {/* Debug info for development */}
      {import.meta.env.DEV && (
        <details className="debug-info">
          <summary>Debug Info</summary>
          <pre>
            Backend Collections: {JSON.stringify(backendCollections, null, 2)}
            {"\n\n"}
            Display Collections: {JSON.stringify(displayCollections, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
};

export default SmartCollectionList;
