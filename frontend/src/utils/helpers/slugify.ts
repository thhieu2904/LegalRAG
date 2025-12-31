/**
 * Slugify Utility
 * Convert Vietnamese text to URL-friendly slug
 */

/**
 * Vietnamese character map for conversion to ASCII
 */
const vietnameseMap: Record<string, string> = {
  // Lowercase vowels with diacritics
  à: 'a',
  á: 'a',
  ả: 'a',
  ã: 'a',
  ạ: 'a',
  ă: 'a',
  ằ: 'a',
  ắ: 'a',
  ẳ: 'a',
  ẵ: 'a',
  ặ: 'a',
  â: 'a',
  ầ: 'a',
  ấ: 'a',
  ẩ: 'a',
  ẫ: 'a',
  ậ: 'a',
  đ: 'd',
  è: 'e',
  é: 'e',
  ẻ: 'e',
  ẽ: 'e',
  ẹ: 'e',
  ê: 'e',
  ề: 'e',
  ế: 'e',
  ể: 'e',
  ễ: 'e',
  ệ: 'e',
  ì: 'i',
  í: 'i',
  ỉ: 'i',
  ĩ: 'i',
  ị: 'i',
  ò: 'o',
  ó: 'o',
  ỏ: 'o',
  õ: 'o',
  ọ: 'o',
  ô: 'o',
  ồ: 'o',
  ố: 'o',
  ổ: 'o',
  ỗ: 'o',
  ộ: 'o',
  ơ: 'o',
  ờ: 'o',
  ớ: 'o',
  ở: 'o',
  ỡ: 'o',
  ợ: 'o',
  ù: 'u',
  ú: 'u',
  ủ: 'u',
  ũ: 'u',
  ụ: 'u',
  ư: 'u',
  ừ: 'u',
  ứ: 'u',
  ử: 'u',
  ữ: 'u',
  ự: 'u',
  ỳ: 'y',
  ý: 'y',
  ỷ: 'y',
  ỹ: 'y',
  ỵ: 'y',
  // Uppercase vowels with diacritics
  À: 'A',
  Á: 'A',
  Ả: 'A',
  Ã: 'A',
  Ạ: 'A',
  Ă: 'A',
  Ằ: 'A',
  Ắ: 'A',
  Ẳ: 'A',
  Ẵ: 'A',
  Ặ: 'A',
  Â: 'A',
  Ầ: 'A',
  Ấ: 'A',
  Ẩ: 'A',
  Ẫ: 'A',
  Ậ: 'A',
  Đ: 'D',
  È: 'E',
  É: 'E',
  Ẻ: 'E',
  Ẽ: 'E',
  Ẹ: 'E',
  Ê: 'E',
  Ề: 'E',
  Ế: 'E',
  Ể: 'E',
  Ễ: 'E',
  Ệ: 'E',
  Ì: 'I',
  Í: 'I',
  Ỉ: 'I',
  Ĩ: 'I',
  Ị: 'I',
  Ò: 'O',
  Ó: 'O',
  Ỏ: 'O',
  Õ: 'O',
  Ọ: 'O',
  Ô: 'O',
  Ồ: 'O',
  Ố: 'O',
  Ổ: 'O',
  Ỗ: 'O',
  Ộ: 'O',
  Ơ: 'O',
  Ờ: 'O',
  Ớ: 'O',
  Ở: 'O',
  Ỡ: 'O',
  Ợ: 'O',
  Ù: 'U',
  Ú: 'U',
  Ủ: 'U',
  Ũ: 'U',
  Ụ: 'U',
  Ư: 'U',
  Ừ: 'U',
  Ứ: 'U',
  Ử: 'U',
  Ữ: 'U',
  Ự: 'U',
  Ỳ: 'Y',
  Ý: 'Y',
  Ỷ: 'Y',
  Ỹ: 'Y',
  Ỵ: 'Y',
};

/**
 * Convert Vietnamese text to ASCII slug
 * @param text - Input text (e.g., "Bộ luật Dân sự")
 * @returns Slugified text (e.g., "bo-luat-dan-su")
 *
 * @example
 * slugify("Bộ luật Dân sự") // "bo-luat-dan-su"
 * slugify("Văn bản Pháp luật") // "van-ban-phap-luat"
 * slugify("Thủ tục Hành chính") // "thu-tuc-hanh-chinh"
 */
export function slugify(text: string): string {
  if (!text) return '';

  let slug = text.trim().toLowerCase();

  // Replace Vietnamese characters with ASCII
  slug = slug
    .split('')
    .map((char) => vietnameseMap[char] || char)
    .join('');

  // Remove special characters, keep only alphanumeric and spaces
  slug = slug.replace(/[^a-z0-9\s-]/g, '');

  // Replace multiple spaces/hyphens with single hyphen
  slug = slug.replace(/[\s-]+/g, '-');

  // Remove leading/trailing hyphens
  slug = slug.replace(/^-+|-+$/g, '');

  return slug;
}

/**
 * Validate if slug format is correct
 * @param slug - Slug to validate
 * @returns True if valid, false otherwise
 */
export function isValidSlug(slug: string): boolean {
  return /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug);
}

/**
 * Generate unique slug with counter suffix if needed
 * @param text - Input text
 * @param existingSlugs - Array of existing slugs to check against
 * @returns Unique slug
 *
 * @example
 * generateUniqueSlug("Test", ["test"]) // "test-1"
 * generateUniqueSlug("Test", ["test", "test-1"]) // "test-2"
 */
export function generateUniqueSlug(text: string, existingSlugs: string[]): string {
  const baseSlug = slugify(text);
  let slug = baseSlug;
  let counter = 1;

  while (existingSlugs.includes(slug)) {
    slug = `${baseSlug}-${counter}`;
    counter++;
  }

  return slug;
}
