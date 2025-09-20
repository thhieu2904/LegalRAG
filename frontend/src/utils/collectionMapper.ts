/**
 * Collection Display Name Mapper
 * Frontend utility để mapping collection keys → display names
 * Sử dụng danh sách collections thật từ backend API
 */

interface CollectionMapping {
  [key: string]: string;
}

// Cache cho collections từ API
let collectionsCache: string[] | null = null;

/**
 * Get collections từ backend API
 */
export async function fetchCollections(): Promise<string[]> {
  try {
    const response = await fetch("/api/v1/collections");
    const data = await response.json();
    collectionsCache = data.collections || [];
    return collectionsCache || [];
  } catch (error) {
    console.error("Error fetching collections:", error);
    return [];
  }
}

/**
 * Generate display name từ collection key
 */
export function generateDisplayName(collectionKey: string): string {
  // Common Vietnamese legal terms mapping
  const legalTerms: CollectionMapping = {
    // Document types
    quy_trinh: "Quy trình",
    luat: "Luật",
    nghi_dinh: "Nghị định",
    thong_tu: "Thông tư",
    quyet_dinh: "Quyết định",
    huong_dan: "Hướng dẫn",

    // Legal domains
    boi_thuong: "Bồi thường",
    cap: "Cấp",
    ho_tich: "Hộ tịch",
    xa: "Xã",
    tp: "Thành phố",
    chung_thuc: "Chứng thực",
    cong_chung: "Công chứng",
    dau_gia: "Đấu giá",
    tai_san: "Tài sản",
    luat_su: "Luật sư",
    nuoi: "Nuôi",
    con: "Con",
    pbgdpl: "PBGDPL",
    htpldn: "HTPLDN",
    quan_tai: "Quan tài",
    vien: "Viện",
    thua: "Thừa",
    phat_lai: "Phát lại",
    trong_tai: "Trọng tài",
    thuong_mai: "Thương mại",
    tu_van: "Tư vấn",
    phap_luat: "Pháp luật",

    // Common terms
    nn: "NN",
    va: "và",
    cua: "của",
    den: "đến",
    tai: "tại",
    cho: "cho",
    theo: "theo",
    voi: "với",
    trong: "trong",
    ngoai: "ngoài",
    tren: "trên",
    duoi: "dưới",
    giua: "giữa",
    sau: "sau",
    truoc: "trước",
  };

  // Split by underscore and map each part
  const parts = collectionKey.split("_");
  const mappedParts = parts.map((part) => {
    // Try to map the term, fallback to title case
    return legalTerms[part] || part.charAt(0).toUpperCase() + part.slice(1);
  });

  return mappedParts.join(" ");
}

/**
 * Get display name with validation
 */
export async function getCollectionDisplayName(
  collectionKey: string
): Promise<string> {
  // Ensure we have collections list
  if (!collectionsCache) {
    await fetchCollections();
  }

  // Validate collection exists
  if (collectionsCache && !collectionsCache.includes(collectionKey)) {
    console.warn(
      `Collection '${collectionKey}' not found in available collections`
    );
  }

  return generateDisplayName(collectionKey);
}

/**
 * Get all collections with display names
 */
export async function getAllCollectionsWithDisplayNames(): Promise<
  Array<{ key: string; displayName: string }>
> {
  const collections = await fetchCollections();

  return collections.map((key) => ({
    key,
    displayName: generateDisplayName(key),
  }));
}
