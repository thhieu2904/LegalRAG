// Curated demo links. These do not assert the current legal validity of a document.
export const PUBLIC_SERVICE_URL = 'https://vpcp.dichvucong.gov.vn/p/home/dvc-trang-chu.html';
export const DOSSIER_LOOKUP_URL = 'https://vpcp.dichvucong.gov.vn/p/home/dvc-tra-cuu-ho-so.html';

export const documentBookmarks = [
  {
    id: 'ho-tich',
    title: 'Luật Hộ tịch',
    number: '60/2014/QH13',
    category: 'Hộ tịch',
    source: 'Công báo Chính phủ',
    url: 'https://congbao.chinhphu.vn/van-ban/luat-so-60-2014-qh13-5264/10513.htm',
  },
  {
    id: 'hon-nhan',
    title: 'Luật Hôn nhân và gia đình',
    number: '52/2014/QH13',
    category: 'Hộ tịch',
    source: 'Công báo Chính phủ',
    url: 'https://congbao.chinhphu.vn/van-ban/luat-so-52-2014-qh13-6127.htm',
  },
  {
    id: 'cu-tru',
    title: 'Luật Cư trú',
    number: '68/2020/QH14',
    category: 'Cư trú',
    source: 'Công báo Chính phủ',
    url: 'https://congbao.chinhphu.vn/van-ban/luat-so-68-2020-qh14-32684/33716.htm',
  },
  {
    id: 'can-cuoc',
    title: 'Luật Căn cước',
    number: '26/2023/QH15',
    category: 'Cư trú',
    source: 'Công báo Chính phủ',
    url: 'https://congbao.chinhphu.vn/van-ban/luat-so-26-2023-qh15-40850/47828.htm',
  },
  {
    id: 'dat-dai',
    title: 'Luật Đất đai',
    number: '31/2024/QH15',
    category: 'Đất đai',
    source: 'Cổng thông tin Chính phủ',
    url: 'https://vanban.chinhphu.vn/?classid=1&docid=211189&orggroupid=1&pageid=27160',
  },
  {
    id: 'mot-cua',
    title: 'Thực hiện thủ tục hành chính theo cơ chế một cửa, một cửa liên thông',
    number: '118/2025/NĐ-CP',
    category: 'Hành chính',
    source: 'Cổng thông tin Chính phủ',
    url: 'https://chinhphu.vn/?docid=213871&pageid=27160',
  },
  {
    id: 'chung-thuc',
    title: 'Cấp bản sao, chứng thực chữ ký và hợp đồng, giao dịch',
    number: '23/2015/NĐ-CP',
    category: 'Hành chính',
    source: 'Cổng thông tin Chính phủ',
    url: 'https://vanban.chinhphu.vn/default.aspx?docid=179100&pageid=27160',
  },
];

export const documentCategories = ['Tất cả', 'Hộ tịch', 'Cư trú', 'Đất đai', 'Hành chính'];

export function normalizeSearch(value: string) {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[đĐ]/g, 'd').toLowerCase();
}
