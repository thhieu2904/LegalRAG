import type { ReactNode } from 'react';
import { ExternalLink, Home, LockKeyhole } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ROUTES } from '@/constants';
import { DOSSIER_LOOKUP_URL, PUBLIC_SERVICE_URL } from './data';
import styles from './PublicPortal.module.css';

interface PortalShellProps {
  title: string;
  description: string;
  lookup?: boolean;
  children: ReactNode;
}

export function PortalShell({ title, description, lookup = false, children }: PortalShellProps) {
  const url = lookup ? DOSSIER_LOOKUP_URL : PUBLIC_SERVICE_URL;

  return (
    <div className={styles.page}>
      <div className={styles.pageInner}>
        <div className={styles.pageHeading}>
          <div><h1>{title}</h1><p className={styles.description}>{description}</p></div>
          <span className={styles.demoBadge}>Bản demo giao diện</span>
        </div>
        <section className={styles.portalFrame} aria-label={title}>
          <div className={styles.browserToolbar}>
            <Link to={ROUTES.HOME} className={styles.browserHome} aria-label="Về danh sách văn bản"><Home size={19} /></Link>
            <div className={styles.addressBar}><LockKeyhole size={14} /><span>{url.replace('https://', '')}</span></div>
            <a className={styles.externalButton} href={url} target="_blank" rel="noopener noreferrer">
              <ExternalLink size={16} /><span>Mở cổng thật</span>
            </a>
          </div>
          <div className={styles.portalBrand}>
            <img src="/demo-dvc-logo.png" alt="Cổng Dịch vụ công Quốc gia" />
            <span className={styles.portalPreview}>Giao diện minh họa</span>
          </div>
          <div className={styles.portalMenu}>
            <Link to={ROUTES.PUBLIC_SERVICES} className={!lookup ? styles.portalMenuActive : ''}>
              <Home size={17} /> Dịch vụ công trực tuyến
            </Link>
            <Link to={ROUTES.DOSSIER_LOOKUP} className={lookup ? styles.portalMenuActive : ''}>
              Tra cứu hồ sơ
            </Link>
          </div>
          {children}
          <div className={styles.portalFootnote}>
            Bản demo của Trung tâm Phục vụ hành chính công xã Long Phú · Chưa kết nối dữ liệu dịch vụ công.
          </div>
        </section>
      </div>
    </div>
  );
}
