import type { ReactNode } from 'react';
import { ExternalLink } from 'lucide-react';
import { DOSSIER_LOOKUP_URL, PUBLIC_SERVICE_URL, SOURCE_LINK_TARGET } from './data';
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
          <a className={styles.externalButton} href={url} target={SOURCE_LINK_TARGET} rel="noopener noreferrer">
            <ExternalLink size={16} /><span>{lookup ? 'Mở trang tra cứu' : 'Mở Cổng Dịch vụ công'}</span>
          </a>
        </div>
        <section className={styles.portalFrame} aria-label={title}>
          {children}
        </section>
      </div>
    </div>
  );
}
