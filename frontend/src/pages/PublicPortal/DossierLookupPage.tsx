import { ArrowRight, FileSearch } from 'lucide-react';
import { PortalShell } from './PortalShell';
import { DOSSIER_LOOKUP_URL, SOURCE_LINK_TARGET } from './data';
import styles from './PublicPortal.module.css';

export default function DossierLookupPage() {
  return (
    <PortalShell title="Tra cứu hồ sơ" description="Theo dõi tiến độ giải quyết hồ sơ tại Cổng Dịch vụ công Quốc gia." lookup>
      <div className={styles.serviceContent}>
        <div className={styles.lookupIcon}><FileSearch size={31} /></div>
        <h2>Tra cứu hồ sơ đã nộp</h2>
        <p className={styles.description}>
          Chuẩn bị mã hồ sơ trên giấy tiếp nhận và hẹn trả kết quả.
          Nhập mã tại trang tra cứu của Cổng Dịch vụ công Quốc gia để xem thông tin chính thức.
        </p>
        <div className={styles.serviceActions}>
          <div><FileSearch size={24} /><div><strong>Kiểm tra tình trạng hồ sơ</strong><p>Tra cứu bằng mã tiếp nhận của bạn.</p></div></div>
          <a href={DOSSIER_LOOKUP_URL} target={SOURCE_LINK_TARGET} rel="noopener noreferrer">Tra cứu hồ sơ <ArrowRight size={17} /></a>
        </div>
      </div>
    </PortalShell>
  );
}
