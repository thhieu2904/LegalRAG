/**
 * 🎨 COLLECTION MAPPING SERVICE - FRONTEND DRIVEN
 *
 * This service handles ALL presentation logic for collections.
 * Backend only provides business data, frontend decides how to display.
 */

// Types for type safety
export interface BackendCollection {
  id: string;
  document_count: number;
  question_count: number;
  status: "active" | "empty" | "disabled";
  last_updated?: string;
  data_version: string;
  path: string;
}

export interface CollectionMapping {
  displayName: string;
  shortName: string;
  description: string;
  icon: string;
  category: string;
  keywords: string[];
  color: string;
  priority: number;
  visible: boolean;
  adminManaged: boolean;
}

export interface DisplayCollection {
  id: string;
  displayName: string;
  shortName: string;
  description: string;
  icon: string;
  category: string;
  keywords: string[];
  color: string;
  documentCount: number;
  questionCount: number;
  status: string;
  lastUpdated?: string;
  priority: number;
  visible: boolean;
}

// Default mapping configuration
const DEFAULT_MAPPINGS: Record<string, CollectionMapping> = {
  quy_trinh_cap_ho_tich_cap_xa: {
    displayName: "Hộ tịch cấp xã",
    shortName: "ho_tich_cap_xa",
    description:
      "Thủ tục về khai sinh, kết hôn, khai tử và các dịch vụ hộ tịch",
    icon: "🏛️",
    category: "dich_vu_hanh_chinh",
    keywords: ["khai sinh", "kết hôn", "khai tử", "hộ tịch", "đăng ký"],
    color: "#3B82F6",
    priority: 1,
    visible: true,
    adminManaged: false,
  },
  quy_trinh_chung_thuc: {
    displayName: "Chứng thực",
    shortName: "chung_thuc",
    description: "Thủ tục chứng thực hợp đồng, chữ ký, bản sao giấy tờ",
    icon: "📋",
    category: "phap_ly",
    keywords: ["chứng thực", "hợp đồng", "chữ ký", "bản sao"],
    color: "#10B981",
    priority: 2,
    visible: true,
    adminManaged: false,
  },
  quy_trinh_nuoi_con_nuoi: {
    displayName: "Nuôi con nuôi",
    shortName: "nuoi_con_nuoi",
    description: "Thủ tục nhận con nuôi và giám hộ trẻ em",
    icon: "👶",
    category: "gia_dinh",
    keywords: ["nuôi con nuôi", "nhận con nuôi", "giám hộ", "trẻ em"],
    color: "#F59E0B",
    priority: 3,
    visible: true,
    adminManaged: false,
  },
};

// Category mappings for grouping
const CATEGORY_MAPPINGS: Record<
  string,
  { name: string; icon: string; color: string }
> = {
  dich_vu_hanh_chinh: {
    name: "Dịch vụ hành chính",
    icon: "🏛️",
    color: "#3B82F6",
  },
  phap_ly: {
    name: "Pháp lý",
    icon: "⚖️",
    color: "#10B981",
  },
  gia_dinh: {
    name: "Gia đình & Trẻ em",
    icon: "👨‍👩‍👧‍👦",
    color: "#F59E0B",
  },
};

class CollectionMappingService {
  private mappings: Record<string, CollectionMapping> = {};

  constructor() {
    this.loadMappings();
  }

  /**
   * Initialize mappings from localStorage or defaults
   */
  private loadMappings(): void {
    try {
      const stored = localStorage.getItem("collection_mappings");
      if (stored) {
        const parsed = JSON.parse(stored);
        this.mappings = { ...DEFAULT_MAPPINGS, ...parsed };
      } else {
        this.mappings = { ...DEFAULT_MAPPINGS };
      }
    } catch (error) {
      console.warn("Failed to load collection mappings from storage:", error);
      this.mappings = { ...DEFAULT_MAPPINGS };
    }
  }

  /**
   * Map backend collection to frontend display format
   */
  mapCollectionForDisplay(
    backendCollection: BackendCollection
  ): DisplayCollection {
    const mapping = this.mappings[backendCollection.id];

    if (!mapping) {
      // Auto-generate mapping for unknown collections
      const autoMapping = this.generateAutoMapping(backendCollection.id);
      this.mappings[backendCollection.id] = autoMapping;
      this.saveMappings();
    }

    const finalMapping = this.mappings[backendCollection.id];

    return {
      id: backendCollection.id,
      displayName: finalMapping.displayName,
      shortName: finalMapping.shortName,
      description: finalMapping.description,
      icon: finalMapping.icon,
      category: finalMapping.category,
      keywords: finalMapping.keywords,
      color: finalMapping.color,
      documentCount: backendCollection.document_count,
      questionCount: backendCollection.question_count,
      status: backendCollection.status,
      lastUpdated: backendCollection.last_updated,
      priority: finalMapping.priority,
      visible: finalMapping.visible,
    };
  }

  /**
   * Map multiple collections with sorting and filtering
   */
  mapCollectionsForDisplay(
    backendCollections: BackendCollection[]
  ): DisplayCollection[] {
    return backendCollections
      .map((collection) => this.mapCollectionForDisplay(collection))
      .filter((collection) => collection.visible) // Only show visible collections
      .sort((a, b) => a.priority - b.priority); // Sort by priority
  }

  /**
   * Get collections grouped by category
   */
  getCollectionsByCategory(
    backendCollections: BackendCollection[]
  ): Record<string, DisplayCollection[]> {
    const mapped = this.mapCollectionsForDisplay(backendCollections);
    const grouped: Record<string, DisplayCollection[]> = {};

    mapped.forEach((collection) => {
      if (!grouped[collection.category]) {
        grouped[collection.category] = [];
      }
      grouped[collection.category].push(collection);
    });

    return grouped;
  }

  /**
   * Get category information
   */
  getCategoryInfo(categoryKey: string) {
    return (
      CATEGORY_MAPPINGS[categoryKey] || {
        name: categoryKey
          .replace(/_/g, " ")
          .replace(/\b\w/g, (l) => l.toUpperCase()),
        icon: "📁",
        color: "#6B7280",
      }
    );
  }

  /**
   * Auto-generate mapping for unknown collections
   */
  private generateAutoMapping(collectionId: string): CollectionMapping {
    // Remove common prefixes
    let cleanName = collectionId;
    const prefixes = ["quy_trinh_", "thu_tuc_", "dich_vu_"];
    prefixes.forEach((prefix) => {
      if (cleanName.startsWith(prefix)) {
        cleanName = cleanName.substring(prefix.length);
      }
    });

    // Generate display name
    const displayName = cleanName
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");

    return {
      displayName,
      shortName: cleanName,
      description: `Thủ tục về ${displayName.toLowerCase()}`,
      icon: "📄",
      category: "khac",
      keywords: cleanName.split("_"),
      color: "#6B7280",
      priority: 999,
      visible: true,
      adminManaged: true, // Mark as admin managed since it's auto-generated
    };
  }

  /**
   * Update mapping for a collection (Admin function)
   */
  updateMapping(
    collectionId: string,
    mapping: Partial<CollectionMapping>
  ): void {
    if (!this.mappings[collectionId]) {
      this.mappings[collectionId] = this.generateAutoMapping(collectionId);
    }

    this.mappings[collectionId] = {
      ...this.mappings[collectionId],
      ...mapping,
    };

    this.saveMappings();
  }

  /**
   * Get mapping for editing (Admin function)
   */
  getMapping(collectionId: string): CollectionMapping | null {
    return this.mappings[collectionId] || null;
  }

  /**
   * Get all mappings (Admin function)
   */
  getAllMappings(): Record<string, CollectionMapping> {
    return { ...this.mappings };
  }

  /**
   * Save mappings to localStorage
   */
  private saveMappings(): void {
    try {
      localStorage.setItem(
        "collection_mappings",
        JSON.stringify(this.mappings)
      );
    } catch (error) {
      console.error("Failed to save collection mappings:", error);
    }
  }

  /**
   * Export mappings for backup (Admin function)
   */
  exportMappings(): string {
    return JSON.stringify(this.mappings, null, 2);
  }

  /**
   * Import mappings from backup (Admin function)
   */
  importMappings(mappingsJson: string): boolean {
    try {
      const imported = JSON.parse(mappingsJson);
      this.mappings = { ...this.mappings, ...imported };
      this.saveMappings();
      return true;
    } catch (error) {
      console.error("Failed to import mappings:", error);
      return false;
    }
  }

  /**
   * Reset to default mappings (Admin function)
   */
  resetToDefaults(): void {
    this.mappings = { ...DEFAULT_MAPPINGS };
    this.saveMappings();
  }

  /**
   * Search collections by keyword
   */
  searchCollections(
    backendCollections: BackendCollection[],
    keyword: string
  ): DisplayCollection[] {
    const mapped = this.mapCollectionsForDisplay(backendCollections);
    const searchTerm = keyword.toLowerCase();

    return mapped.filter(
      (collection) =>
        collection.displayName.toLowerCase().includes(searchTerm) ||
        collection.description.toLowerCase().includes(searchTerm) ||
        collection.keywords.some((k) => k.toLowerCase().includes(searchTerm))
    );
  }
}

// Export singleton instance
export const collectionMappingService = new CollectionMappingService();

// Export types and defaults for admin use
export { CATEGORY_MAPPINGS, DEFAULT_MAPPINGS };
