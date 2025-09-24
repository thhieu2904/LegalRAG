/**
 * 🏛️ COLLECTION MAPPING API
 * Service for mapping collection IDs to readable Vietnamese names
 * and formatting document names for display
 */

// Collection ID to Vietnamese name mapping
const COLLECTION_NAME_MAPPING: { [key: string]: string } = {
  quy_trinh_boi_thuong_nn: "Bồi thường nhà nước",
  quy_trinh_cap_ho_tich_cap_xa: "Hộ tịch cấp xã",
  quy_trinh_chung_thuc: "Chứng thực",
  quy_trinh_cong_chung: "Công chứng",
  quy_trinh_dau_gia_tai_san: "Đấu giá tài sản",
  quy_trinh_ho_tich_cap_tp: "Hộ tịch cấp thành phố",
  quy_trinh_luat_su: "Luật sư",
  quy_trinh_nuoi_con_nuoi: "Nuôi con nuôi",
  quy_trinh_pbgdpl_htpldn: "Phòng bảo gồm đặc lợi HTPL DN",
  quy_trinh_quan_tai_vien: "Quan tài viên",
  quy_trinh_thua_phat_lai: "Thừa phát lại",
  quy_trinh_trong_tai_thuong_mai: "Trọng tài thương mại",
  quy_trinh_tu_van_phap_luat: "Tư vấn pháp luật",
};

/**
 * Convert collection ID to readable Vietnamese name
 * @param collectionId - The collection identifier (e.g., "quy_trinh_cap_ho_tich_cap_xa")
 * @returns Formatted Vietnamese name (e.g., "Hộ tịch cấp xã")
 */
export const formatCollectionName = (collectionId: string): string => {
  const mappedName = COLLECTION_NAME_MAPPING[collectionId];

  if (mappedName) {
    return mappedName;
  }

  // Fallback: convert underscores to spaces and capitalize
  return collectionId
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
};

/**
 * Format document file path to display name with index
 * Removes DOC_xxx prefixes and .json extensions
 * @param filePath - Full file path (e.g., "/app/data/storage/collections/quy_trinh_cap_ho_tich_cap_xa/documents/DOC_001/01. Đăng ký khai sinh.json")
 * @param index - Index number for display (0-based)
 * @returns Formatted display name (e.g., "1. Đăng ký khai sinh")
 */
export const formatDocumentName = (filePath: string, index: number): string => {
  try {
    // Extract filename from path
    const parts = filePath.split("/");
    const fileName = parts[parts.length - 1] || filePath;

    // Remove .json extension
    const nameWithoutExtension = fileName.replace(/\.json$/, "");

    // Remove DOC_xxx pattern at the start if present
    const cleanName = nameWithoutExtension.replace(/^\d+\.\s*/, "");

    // Return with 1-based index
    return `${index + 1}. ${cleanName}`;
  } catch (error) {
    console.warn("Error formatting document name:", error);
    return `${index + 1}. ${filePath}`;
  }
};

/**
 * Get all available collection names
 * @returns Array of collection IDs
 */
export const getAvailableCollections = (): string[] => {
  return Object.keys(COLLECTION_NAME_MAPPING);
};

/**
 * Get collection display name by ID
 * @param collectionId - Collection identifier
 * @returns Display name or null if not found
 */
export const getCollectionDisplayName = (
  collectionId: string
): string | null => {
  return COLLECTION_NAME_MAPPING[collectionId] || null;
};

/**
 * Check if collection ID exists in mapping
 * @param collectionId - Collection identifier to check
 * @returns True if collection exists in mapping
 */
export const isValidCollection = (collectionId: string): boolean => {
  return collectionId in COLLECTION_NAME_MAPPING;
};
