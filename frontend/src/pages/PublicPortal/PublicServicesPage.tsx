import { ArrowRight, ClipboardCheck, CreditCard, FileText, Send } from 'lucide-react';
import { PortalShell } from './PortalShell';
import {
  documentBookmarks, DOSSIER_LOOKUP_URL, ONLINE_SERVICES_URL,
  PAYMENT_URL, SOURCE_LINK_TARGET,
} from './data';
import styles from './PublicPortal.module.css';

const actions = [
  { title: 'Nộp hồ sơ trực tuyến', description: 'Tìm thủ tục và nộp hồ sơ tại cổng quốc gia', icon: Send, url: ONLINE_SERVICES_URL },
  { title: 'Tra cứu hồ sơ', description: 'Theo dõi hồ sơ đã nộp bằng mã tiếp nhận', icon: ClipboardCheck, url: DOSSIER_LOOKUP_URL },
  { title: 'Thanh toán trực tuyến', description: 'Thanh toán phí, lệ phí tại cổng quốc gia', icon: CreditCard, url: PAYMENT_URL },
];

export default function PublicServicesPage() {
  return (
    <PortalShell title="Cổng Dịch vụ công" description="Truy cập các dịch vụ trực tuyến của Cổng Dịch vụ công Quốc gia.">
      <div className={styles.serviceContent}>
        <div className={styles.serviceSectionHeading}><h2>Bạn cần thực hiện việc gì?</h2></div>
        <div className={`${styles.serviceGrid} ${styles.serviceActionGrid}`}>
          {actions.map(({ title, description, icon: Icon, url }) => (
            <a key={url} className={styles.serviceCard} href={url} target={SOURCE_LINK_TARGET} rel="noopener noreferrer">
              <div className={styles.serviceIcon}><Icon size={27} /></div>
              <h3>{title}</h3><p>{description}</p>
              <span>Mở dịch vụ <ArrowRight size={16} /></span>
            </a>
          ))}
        </div>
        <div className={styles.serviceSectionHeading} style={{ marginTop: '2rem' }}><h2>Thủ tục thường dùng</h2></div>
        <div className={styles.serviceGrid}>
          {documentBookmarks.map(document => (
            <a key={document.id} className={styles.serviceCard} href={document.url} target={SOURCE_LINK_TARGET} rel="noopener noreferrer">
              <div className={styles.serviceIcon}><FileText size={27} /></div>
              <h3>{document.title}</h3><p>{document.category}</p>
              <span>Xem thủ tục <ArrowRight size={16} /></span>
            </a>
          ))}
        </div>
      </div>
    </PortalShell>
  );
}
