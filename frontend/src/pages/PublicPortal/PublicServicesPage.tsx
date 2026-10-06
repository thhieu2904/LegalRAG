import { useState } from 'react';
import {
  ArrowRight, Baby, BriefcaseBusiness, ClipboardCheck, HeartHandshake,
  House, IdCard, Search, ShieldCheck, Users,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { ROUTES } from '@/constants';
import { PortalShell } from './PortalShell';
import { normalizeSearch, PUBLIC_SERVICE_URL } from './data';
import styles from './PublicPortal.module.css';

const services = [
  { title: 'Hộ tịch', description: 'Khai sinh, khai tử, trích lục hộ tịch', icon: Baby, group: '750', audience: 'citizen' },
  { title: 'Cư trú và căn cước', description: 'Cư trú, giấy tờ tùy thân', icon: IdCard, group: '753', audience: 'citizen' },
  { title: 'Hôn nhân và gia đình', description: 'Đăng ký kết hôn, tình trạng hôn nhân', icon: HeartHandshake, group: '754', audience: 'citizen' },
  { title: 'Nhà ở và đất đai', description: 'Đất đai, xây dựng, nhà ở', icon: House, group: '755', audience: 'citizen' },
  { title: 'Khởi sự kinh doanh', description: 'Thành lập, đăng ký kinh doanh', icon: BriefcaseBusiness, group: '760', audience: 'business' },
  { title: 'Lao động và bảo hiểm', description: 'Lao động, bảo hiểm xã hội', icon: ShieldCheck, group: '761', audience: 'business' },
];

export default function PublicServicesPage() {
  const [query, setQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [audience, setAudience] = useState('citizen');
  const visibleServices = services.filter(service =>
    service.audience === audience &&
    normalizeSearch(`${service.title} ${service.description}`).includes(normalizeSearch(submittedQuery.trim()))
  );

  return (
    <PortalShell title="Hành chính công" description="Truy cập dịch vụ công và các thủ tục hành chính trực tuyến.">
      <section className={styles.serviceHero}>
        <p className={styles.portalEyebrow}>DỊCH VỤ CÔNG TRỰC TUYẾN</p>
        <h2>Thủ tục hành chính, trong tầm tay</h2>
        <p>Tìm thủ tục bạn cần và chuyển đến Cổng Dịch vụ công Quốc gia.</p>
        <form className={styles.serviceSearch} onSubmit={event => {
          event.preventDefault(); setSubmittedQuery(query);
        }}>
          <Search size={21} aria-hidden="true" />
          <input
            aria-label="Tìm nhóm dịch vụ"
            placeholder="Nhập thủ tục hoặc dịch vụ bạn cần tìm..."
            value={query}
            onChange={event => setQuery(event.target.value)}
            type="search"
          />
          <button type="submit">Tìm kiếm</button>
        </form>
      </section>
      <div className={styles.serviceContent}>
        <div className={styles.serviceSectionHeading}>
          <h2>Nhóm dịch vụ thường dùng</h2>
          <div className={styles.audienceSwitch} role="group" aria-label="Đối tượng sử dụng">
            <button className={audience === 'citizen' ? styles.audienceActive : ''} aria-pressed={audience === 'citizen'} onClick={() => setAudience('citizen')}><Users size={16} /> Công dân</button>
            <button className={audience === 'business' ? styles.audienceActive : ''} aria-pressed={audience === 'business'} onClick={() => setAudience('business')}><BriefcaseBusiness size={16} /> Doanh nghiệp</button>
          </div>
        </div>
        <div className={styles.serviceGrid}>
          {visibleServices.map(({ title, description, icon: Icon, group }) => (
            <a
              key={title}
              className={styles.serviceCard}
              href={`https://vpcp.dichvucong.gov.vn/p/home/dvc-chi-tiet-nhom-su-kien-cho-${audience === 'business' ? 'doanh-nghiep' : 'cong-dan'}.html?group=${group}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <div className={styles.serviceIcon}><Icon size={27} /></div>
              <h3>{title}</h3><p>{description}</p>
              <span>Xem trên cổng dịch vụ công <ArrowRight size={16} /></span>
            </a>
          ))}
        </div>
        {visibleServices.length === 0 && (
          <div className={styles.emptyState}>
            <Search size={28} /><h3>Chưa có nhóm dịch vụ phù hợp trong demo</h3>
            <button className={styles.textButton} onClick={() => { setQuery(''); setSubmittedQuery(''); }}>Xem tất cả nhóm dịch vụ <ArrowRight size={16} /></button>
          </div>
        )}
        <div className={styles.serviceActions}>
          <div><ClipboardCheck size={24} /><div><strong>Đã nộp hồ sơ?</strong><p>Xem tiến độ tại tab Kiểm tra hồ sơ.</p></div></div>
          <Link to={ROUTES.DOSSIER_LOOKUP}>Kiểm tra hồ sơ <ArrowRight size={17} /></Link>
        </div>
        <a className={styles.allServices} href={PUBLIC_SERVICE_URL} target="_blank" rel="noopener noreferrer">Xem toàn bộ dịch vụ tại cổng quốc gia <ArrowRight size={16} /></a>
      </div>
    </PortalShell>
  );
}
