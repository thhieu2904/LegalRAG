// Public destinations reviewed against the Long Phu OA menu on 2026-10-06.
// Do not derive procedure IDs or substitute a simulated lookup result.
export const PUBLIC_SERVICE_URL = 'https://dichvucong.gov.vn/';
export const ONLINE_SERVICES_URL = 'https://dichvucong.gov.vn/dvc-dich-vu-cong-truc-tuyen';
export const DOSSIER_LOOKUP_URL = 'https://dichvucong.gov.vn/tra-cuu-ho-so';
export const PAYMENT_URL = 'https://dichvucong.gov.vn/thanh-toan-truc-tuyen';
export const SOURCE_LINK_TARGET = '_blank';

export const documentBookmarks = [
  {
    id: 'dang-ky-khai-sinh',
    title: 'Đăng ký khai sinh',
    number: 'Thủ tục hành chính',
    category: 'Hộ tịch',
    source: 'Cổng Dịch vụ công Quốc gia',
    url: 'https://dichvucong.gov.vn/tim-kiem-thu-tuc-hanh-chinh?formalityId=019d2bfd-3fe0-70ac-b9d6-5e9e20d6eef7&formalityCaseId=019dd20f-6f0d-72cd-9eca-fbc9d34053a6',
  },
  {
    id: 'trich-luc-ho-tich',
    title: 'Trích lục hộ tịch',
    number: 'Thủ tục hành chính',
    category: 'Hộ tịch',
    source: 'Cổng Dịch vụ công Quốc gia',
    url: 'https://dichvucong.gov.vn/tim-kiem-thu-tuc-hanh-chinh?formalityId=019d2bfd-867c-72db-b6a7-dcbd8c763807&formalityCaseId=019d62ec-f5f3-7429-afd0-1d8765b43722',
  },
  {
    id: 'dang-ky-khai-tu',
    title: 'Đăng ký khai tử',
    number: 'Thủ tục hành chính',
    category: 'Hộ tịch',
    source: 'Cổng Dịch vụ công Quốc gia',
    url: 'https://dichvucong.gov.vn/tim-kiem-thu-tuc-hanh-chinh?formalityId=019d2bfd-3fac-7489-b53b-9c6c958f2da4&formalityCaseId=019d6642-b82d-75cb-b429-16055891d02c',
  },
  {
    id: 'dang-ky-ket-hon',
    title: 'Đăng ký kết hôn',
    number: 'Thủ tục hành chính',
    category: 'Hôn nhân',
    source: 'Cổng Dịch vụ công Quốc gia',
    url: 'https://dichvucong.gov.vn/tim-kiem-thu-tuc-hanh-chinh?formalityId=019d2bfd-3fac-7489-b53b-a15eb239a6fe&formalityCaseId=019d4346-42c5-71a1-9328-f59faac00421',
  },
  {
    id: 'xac-nhan-hon-nhan',
    title: 'Xác nhận tình trạng hôn nhân',
    number: 'Thủ tục hành chính',
    category: 'Hôn nhân',
    source: 'Cổng Dịch vụ công Quốc gia',
    url: 'https://dichvucong.gov.vn/tim-kiem-thu-tuc-hanh-chinh?formalityId=019d2bfd-6eb3-7019-bf3f-fc58c9ee44b9&formalityCaseId=019db0ca-2db5-749f-8967-9cd8d16b1b80',
  },
  {
    id: 'chung-thuc-ban-sao',
    title: 'Chứng thực bản sao',
    number: 'Thủ tục hành chính',
    category: 'Chứng thực',
    source: 'Cổng Dịch vụ công Quốc gia',
    url: 'https://dichvucong.gov.vn/tim-kiem-thu-tuc-hanh-chinh?formalityId=019d2bfd-8e22-77ef-819f-e49460350904&formalityCaseId=019d2e45-9f74-7708-b183-4a33c75cddf8',
  },
  {
    id: 'chung-thuc-chu-ky',
    title: 'Chứng thực chữ ký',
    number: 'Thủ tục hành chính',
    category: 'Chứng thực',
    source: 'Cổng Dịch vụ công Quốc gia',
    url: 'https://dichvucong.gov.vn/tim-kiem-thu-tuc-hanh-chinh?formalityId=019d2bfd-8e2e-7359-b42f-d5dc8d74741b&formalityCaseId=019e765b-3568-746a-baed-ccf7b0ed2ceb',
  },
];

export const documentCategories = ['Tất cả', ...new Set(documentBookmarks.map(document => document.category))];

export function normalizeSearch(value: string) {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[đĐ]/g, 'd').toLowerCase();
}
