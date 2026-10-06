import { useState } from 'react';
import { ArrowRight, Check, CircleCheck, ClipboardList, FileSearch, Info, Search } from 'lucide-react';
import { PortalShell } from './PortalShell';
import { DOSSIER_LOOKUP_URL } from './data';
import styles from './PublicPortal.module.css';

const DEMO_CODE = 'DEMO-2026-000123';
const progress = [
  { title: 'Đã tiếp nhận', description: 'Hồ sơ đã được ghi nhận', complete: true },
  { title: 'Đang xử lý', description: 'Bộ phận chuyên môn đang xem xét', complete: false },
  { title: 'Có kết quả', description: 'Thông báo khi hoàn tất', complete: false },
];

export default function DossierLookupPage() {
  const [code, setCode] = useState('');
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState('');

  return (
    <PortalShell title="Kiểm tra hồ sơ" description="Tra cứu và theo dõi tiến độ giải quyết hồ sơ dịch vụ công." lookup>
      <div className={styles.lookupContent}>
        <section className={styles.lookupFormPanel}>
          <div className={styles.lookupIcon}><FileSearch size={31} /></div>
          <h2>Tra cứu theo mã hồ sơ</h2>
          <p>Nhập mã được ghi trên giấy tiếp nhận hồ sơ và hẹn trả kết quả.</p>
          <form className={styles.lookupForm} onSubmit={event => {
            event.preventDefault();
            if (!code.trim()) {
              setError('Vui lòng nhập mã hồ sơ hoặc chọn “Dùng mã mẫu”.');
              setResult(null);
              return;
            }
            setError(''); setResult(code.trim());
          }}>
            <label htmlFor="dossier-code">Mã hồ sơ <span aria-hidden="true">*</span></label>
            <div className={styles.lookupInputRow}>
              <input
                id="dossier-code"
                placeholder="Ví dụ: DEMO-2026-000123"
                value={code}
                onChange={event => { setCode(event.target.value); setResult(null); setError(''); }}
                aria-required="true"
                aria-invalid={Boolean(error)}
                aria-describedby={error ? 'dossier-error' : 'lookup-demo-note'}
                autoComplete="off"
                maxLength={80}
              />
              <button className={styles.lookupSubmit} type="submit"><Search size={18} /> Tra cứu</button>
            </div>
            {error && <p id="dossier-error" className={styles.formError} role="alert">{error}</p>}
            <button type="button" className={styles.sampleButton} onClick={() => {
              setCode(DEMO_CODE); setResult(null); setError('');
            }}>Dùng mã mẫu <span>{DEMO_CODE}</span><ArrowRight size={14} /></button>
          </form>
          <div id="lookup-demo-note" className={styles.demoNotice}>
            <Info size={18} /><p>Đây là bản demo. Mọi mã nhập vào đều hiển thị kết quả minh họa, chưa tra cứu dữ liệu thật.</p>
          </div>
        </section>

        <div aria-live="polite" aria-atomic="true">
          {result ? (
            <section className={styles.resultPanel} aria-labelledby="lookup-result-title">
              <div className={styles.resultHeading}>
                <div><p className={styles.eyebrow}>KẾT QUẢ MINH HỌA</p><h2 id="lookup-result-title">Hồ sơ đăng ký khai sinh</h2></div>
                <span className={styles.statusBadge}>Đang xử lý</span>
              </div>
              <dl className={styles.resultDetails}>
                <div><dt>Mã hồ sơ</dt><dd>{result}</dd></div>
                <div><dt>Đơn vị tiếp nhận</dt><dd>Trung tâm PVHCC xã Long Phú</dd></div>
                <div><dt>Ngày tiếp nhận (mẫu)</dt><dd>05/10/2026</dd></div>
                <div><dt>Ngày hẹn trả (mẫu)</dt><dd>08/10/2026</dd></div>
              </dl>
              <h3 className={styles.progressTitle}>Tiến độ giải quyết</h3>
              <ol className={styles.progressList}>
                {progress.map((step, index) => (
                  <li key={step.title} className={`${styles.progressStep} ${index === 1 ? styles.progressCurrent : ''} ${step.complete ? styles.progressComplete : ''}`}>
                    <div className={styles.progressDot}>{step.complete ? <Check size={17} /> : index + 1}</div>
                    <div><strong>{step.title}</strong><span>{step.description}</span></div>
                  </li>
                ))}
              </ol>
              <p className={styles.resultNote}><Info size={16} /> Thông tin trên chỉ phục vụ trình diễn giao diện.</p>
            </section>
          ) : (
            <section className={styles.lookupEmpty}>
              <ClipboardList size={42} aria-hidden="true" />
              <h3>Theo dõi hồ sơ của bạn</h3>
              <p>Kết quả và tiến độ xử lý sẽ hiển thị tại đây.<br />Bạn có thể dùng mã mẫu để xem thử giao diện.</p>
            </section>
          )}
        </div>

        <aside className={styles.lookupHelp}>
          <CircleCheck size={23} />
          <div><h3>Tra cứu hồ sơ thực tế</h3><p>Chuyển đến trang tra cứu của Cổng Dịch vụ công Quốc gia để kiểm tra thông tin chính thức.</p></div>
          <a href={DOSSIER_LOOKUP_URL} target="_blank" rel="noopener noreferrer">Mở trang tra cứu <ArrowRight size={17} /></a>
        </aside>
      </div>
    </PortalShell>
  );
}
