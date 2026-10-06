// Actual TS/TSX configuration and server-rendered UI. No real browser/network.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { test } = require('node:test');
const ts = require('typescript');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const { MemoryRouter } = require('react-router-dom');

const src = path.resolve(__dirname, '../src');
const portal = path.join(src, 'pages/PublicPortal');
const cache = new Map();
function loadSource(filename) {
  let resolved = filename;
  if (!fs.existsSync(resolved)) resolved = ['.ts', '.tsx'].map(extension => filename + extension).find(fs.existsSync);
  assert(resolved, `Missing module ${filename}`);
  if (cache.has(resolved)) return cache.get(resolved).exports;
  const module = { exports: {} };
  cache.set(resolved, module);
  const compiled = ts.transpileModule(fs.readFileSync(resolved, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true },
  }).outputText;
  const localRequire = specifier => {
    if (specifier.endsWith('.module.css')) return { __esModule: true, default: new Proxy({}, { get: (_, key) => key }) };
    if (specifier === '@/constants' || specifier === '@/constants/routes.constants') return loadSource(path.join(src, 'constants/routes.constants.ts'));
    if (specifier.startsWith('.')) return loadSource(path.resolve(path.dirname(resolved), specifier));
    return require(specifier);
  };
  new vm.Script(`(function(module,exports,require){${compiled}\n})`, { filename: resolved })
    .runInThisContext()(module, module.exports, localRequire);
  return module.exports;
}
const data = loadSource(path.join(portal, 'data.ts'));
const { ROUTES, ROUTE_LABELS } = loadSource(path.join(src, 'constants/routes.constants.ts'));
function render(Component) {
  return renderToStaticMarkup(React.createElement(MemoryRouter, null, React.createElement(Component)));
}
const BookmarkPage = loadSource(path.join(portal, 'BookmarksPage.tsx')).default;
const PublicPage = loadSource(path.join(portal, 'PublicServicesPage.tsx')).default;
const LookupPage = loadSource(path.join(portal, 'DossierLookupPage.tsx')).default;

test('canonical portal URLs have no old subdomain or tracking parameters', () => {
  assert.equal(data.PUBLIC_SERVICE_URL, 'https://dichvucong.gov.vn/');
  assert.equal(data.DOSSIER_LOOKUP_URL, 'https://dichvucong.gov.vn/tra-cuu-ho-so');
  assert.equal(data.ONLINE_SERVICES_URL, 'https://dichvucong.gov.vn/dvc-dich-vu-cong-truc-tuyen');
  assert.equal(data.PAYMENT_URL, 'https://dichvucong.gov.vn/thanh-toan-truc-tuyen');
});
test('seven reviewed OA procedures point to explicit procedure/case IDs', () => {
  assert.equal(data.documentBookmarks.length, 7);
  assert.equal(new Set(data.documentBookmarks.map(item => item.id)).size, 7);
  for (const item of data.documentBookmarks) {
    const url = new URL(item.url);
    assert.equal(url.origin, 'https://dichvucong.gov.vn');
    assert.equal(url.pathname, '/tim-kiem-thu-tuc-hanh-chinh');
    assert.deepEqual([...url.searchParams.keys()].sort(), ['formalityCaseId', 'formalityId']);
    for (const value of url.searchParams.values()) assert.match(value, /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/);
  }
  const birth = data.documentBookmarks.find(item => item.id === 'dang-ky-khai-sinh');
  assert.equal(new URL(birth.url).searchParams.get('formalityId'), '019d2bfd-3fe0-70ac-b9d6-5e9e20d6eef7');
  assert.equal(new URL(birth.url).searchParams.get('formalityCaseId'), '019dd20f-6f0d-72cd-9eca-fbc9d34053a6');
});
test('filters follow the new procedure categories; Vietnamese search remains accent-insensitive', () => {
  assert.deepEqual(data.documentCategories, ['Tất cả', 'Hộ tịch', 'Hôn nhân', 'Chứng thực']);
  assert.equal(data.normalizeSearch('Đăng ký khai sinh'), 'dang ky khai sinh');
});
test('tab labels change without breaking existing paths', () => {
  assert.equal(ROUTE_LABELS[ROUTES.PUBLIC_SERVICES], 'Cổng Dịch vụ công');
  assert.equal(ROUTE_LABELS[ROUTES.DOSSIER_LOOKUP], 'Tra cứu hồ sơ');
  assert.equal(ROUTES.PUBLIC_SERVICES, '/hanh-chinh-cong');
  assert.equal(ROUTES.DOSSIER_LOOKUP, '/kiem-tra-ho-so');
  const { PublicNavigation } = loadSource(path.join(src, 'components/layout/PublicNavigation/PublicNavigation.tsx'));
  const html = render(PublicNavigation);
  assert.match(html, /Cổng Dịch vụ công/);
  assert.match(html, /Tra cứu hồ sơ/);
  assert.doesNotMatch(html, />Hành chính công<|>Kiểm tra hồ sơ</);
});
test('all public pages remove temporary labels, fake browser chrome and unsupported iframes', () => {
  for (const Component of [BookmarkPage, PublicPage, LookupPage]) {
    const html = render(Component);
    assert.doesNotMatch(html, /bản demo|bản tạm|giao diện minh họa|kết quả minh họa|DEMO-|demo-dvc-logo|vpcp\.dichvucong|addressBar|browserToolbar|<iframe/i);
  }
});
test('lookup never invents a case status, dates or a result for arbitrary user input', () => {
  const html = render(LookupPage);
  assert.doesNotMatch(html, /<input|<form|Đang xử lý|Đã tiếp nhận|Ngày hẹn trả|Dùng mã mẫu/);
  assert.match(html, /href="https:\/\/dichvucong\.gov\.vn\/tra-cuu-ho-so"/);
});
test('source links open in a new tab safely as selected by the user', () => {
  assert.equal(data.SOURCE_LINK_TARGET, '_blank');
  for (const Component of [BookmarkPage, PublicPage, LookupPage]) {
    const html = render(Component);
    const sourceAnchors = html.match(/<a\b[^>]*href="https:\/\/dichvucong\.gov\.vn[^>]+>/g) || [];
    assert(sourceAnchors.length > 0);
    for (const anchor of sourceAnchors) {
      assert.match(anchor, /target="_blank"/);
      assert.match(anchor, /rel="noopener noreferrer"/);
    }
  }
});
test('new procedure favorites do not overwrite the previous law favorites key', () => {
  const source = fs.readFileSync(path.join(portal, 'BookmarksPage.tsx'), 'utf8');
  assert.match(source, /const STORAGE_KEY = 'legalrag-procedure-bookmarks'/);
  assert.doesNotMatch(source, /const STORAGE_KEY = 'legalrag-document-bookmarks'/);
});
