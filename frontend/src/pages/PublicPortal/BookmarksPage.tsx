import { useEffect, useState } from 'react';
import {
  ArrowRight, Bookmark, BookOpen, ExternalLink, FileText,
  Landmark, MessagesSquare, Search, Star, ClipboardCheck,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { ROUTES } from '@/constants';
import { documentBookmarks, documentCategories, normalizeSearch, SOURCE_LINK_TARGET } from './data';
import styles from './PublicPortal.module.css';

// Keep the previous law-bookmark key untouched when switching to OA procedures.
const STORAGE_KEY = 'legalrag-procedure-bookmarks';

function readSavedBookmarks(): string[] {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    return Array.isArray(value)
      ? [...new Set(value.filter((id): id is string =>
          typeof id === 'string' && documentBookmarks.some(document => document.id === id)))]
      : [];
  } catch {
    return [];
  }
}

export default function BookmarksPage() {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('Tất cả');
  const [saved, setSaved] = useState(readSavedBookmarks);
  const [savedOnly, setSavedOnly] = useState(false);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
    } catch {
      // The link directory remains usable when browser storage is unavailable.
    }
  }, [saved]);

  const visibleDocuments = documentBookmarks.filter(document =>
    (category === 'Tất cả' || document.category === category) &&
    (!savedOnly || saved.includes(document.id)) &&
    normalizeSearch(`${document.title} ${document.number} ${document.category}`)
      .includes(normalizeSearch(query.trim()))
  );

  const toggleSaved = (id: string) => {
    setSaved(current => current.includes(id)
      ? current.filter(savedId => savedId !== id)
      : [...current, id]);
  };

  return (
    <div className={styles.page}>
      <div className={styles.pageInner}>
        <section className={styles.bookmarkHero} aria-labelledby="bookmarks-title">
          <div>
            <p className={styles.eyebrow}><Bookmark size={15} /> TỦ VĂN BẢN</p>
            <h1 id="bookmarks-title">Văn bản thường gặp</h1>
            <p className={styles.description}>
              Tra cứu các thủ tục thường dùng tại Cổng Dịch vụ công Quốc gia.
            </p>
          </div>
          <div className={styles.heroCount}>
            <BookOpen size={27} aria-hidden="true" />
            <div><strong>{String(documentBookmarks.length).padStart(2, '0')}</strong><span>liên kết thủ tục</span></div>
          </div>
        </section>

        <div className={styles.bookmarkLayout}>
          <section className={styles.documentPanel} aria-label="Danh sách văn bản">
            <div className={styles.searchBox}>
              <Search size={20} aria-hidden="true" />
              <input
                aria-label="Tìm văn bản"
                placeholder="Tìm tên thủ tục hoặc lĩnh vực..."
                value={query}
                onChange={event => setQuery(event.target.value)}
                type="search"
              />
              <span className={styles.searchHint}>Tra cứu nhanh</span>
            </div>
            <div className={styles.filterRow} aria-label="Lọc lĩnh vực">
              {documentCategories.map(item => (
                <button
                  key={item}
                  className={`${styles.filterButton} ${category === item ? styles.filterActive : ''}`}
                  aria-pressed={category === item}
                  onClick={() => setCategory(item)}
                >{item}</button>
              ))}
            </div>
            <div className={styles.listHeading}>
              <span aria-live="polite">{visibleDocuments.length} thủ tục{savedOnly ? ' đã đánh dấu' : ''}</span>
              <button
                className={`${styles.savedFilter} ${savedOnly ? styles.savedFilterActive : ''}`}
                aria-pressed={savedOnly}
                onClick={() => setSavedOnly(current => !current)}
              >
                <Star size={15} aria-hidden="true" /> Đã đánh dấu ({saved.length})
              </button>
            </div>
            <ul className={styles.documentList}>
              {visibleDocuments.map(document => (
                <li key={document.id} className={styles.documentRow}>
                  <div className={styles.documentIcon}><FileText size={23} aria-hidden="true" /></div>
                  <a className={styles.documentLink} href={document.url} target={SOURCE_LINK_TARGET} rel="noopener noreferrer">
                    <h2>{document.title}</h2>
                    <div className={styles.documentMeta}>
                      <span>{document.number}</span><span className={styles.metaDot}>·</span><span>{document.source}</span>
                    </div>
                  </a>
                  <span className={styles.categoryTag}>{document.category}</span>
                  <button
                    className={`${styles.starButton} ${saved.includes(document.id) ? styles.starSaved : ''}`}
                    aria-label={`${saved.includes(document.id) ? 'Bỏ đánh dấu' : 'Đánh dấu'} ${document.title}`}
                    aria-pressed={saved.includes(document.id)}
                    title="Đánh dấu văn bản"
                    onClick={() => toggleSaved(document.id)}
                  >
                    <Star size={18} fill={saved.includes(document.id) ? 'currentColor' : 'none'} />
                  </button>
                  <a
                    className={styles.openDocument}
                    href={document.url}
                    target={SOURCE_LINK_TARGET}
                    rel="noopener noreferrer"
                    aria-label={`Mở ${document.title} tại trang nguồn`}
                    title="Mở trang nguồn"
                  ><ExternalLink size={17} /></a>
                </li>
              ))}
            </ul>
            {visibleDocuments.length === 0 && (
              <div className={styles.emptyState}>
                <Search size={30} aria-hidden="true" />
                <h2>Chưa có thủ tục phù hợp</h2>
                <p>Thử từ khóa khác hoặc xem toàn bộ danh sách.</p>
                <button className={styles.textButton} onClick={() => {
                  setQuery(''); setCategory('Tất cả'); setSavedOnly(false);
                }}>Xem tất cả thủ tục <ArrowRight size={16} /></button>
              </div>
            )}
            <p className={styles.listNote}><ExternalLink size={14} /> Xem thông tin chính thức tại Cổng Dịch vụ công Quốc gia.</p>
          </section>

          <aside className={styles.bookmarkAside}>
            <section className={styles.quickAccess}>
              <p className={styles.eyebrow}>TRUY CẬP NHANH</p>
              <h2>Bạn cần hỗ trợ gì?</h2>
              <Link to={ROUTES.PUBLIC_SERVICES} className={styles.quickLink}>
                <Landmark size={22} /><div><strong>Cổng Dịch vụ công</strong><span>Nộp hồ sơ trực tuyến</span></div><ArrowRight size={17} />
              </Link>
              <Link to={ROUTES.DOSSIER_LOOKUP} className={styles.quickLink}>
                <ClipboardCheck size={22} /><div><strong>Tra cứu hồ sơ</strong><span>Theo dõi tiến độ xử lý</span></div><ArrowRight size={17} />
              </Link>
              <Link to={ROUTES.CHAT} className={styles.quickLink}>
                <MessagesSquare size={22} /><div><strong>Hỏi Trợ lý AI</strong><span>Giải đáp thủ tục, pháp luật</span></div><ArrowRight size={17} />
              </Link>
            </section>
            <section className={styles.bookmarkTip}>
              <Star size={21} aria-hidden="true" />
              <h3>Giữ thủ tục bạn hay dùng</h3>
              <p>Bấm ngôi sao cạnh thủ tục, sau đó chọn “Đã đánh dấu” để tìm lại nhanh hơn.</p>
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}
