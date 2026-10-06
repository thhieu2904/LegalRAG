import { BookMarked, ClipboardCheck, Landmark, MessagesSquare } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { ROUTES, ROUTE_LABELS } from '@/constants/routes.constants';
import styles from './PublicNavigation.module.css';

const tabs = [
  { to: ROUTES.HOME, icon: BookMarked },
  { to: ROUTES.PUBLIC_SERVICES, icon: Landmark },
  { to: ROUTES.CHAT, icon: MessagesSquare },
  { to: ROUTES.DOSSIER_LOOKUP, icon: ClipboardCheck },
];

export const PublicNavigation = () => (
  <nav className={styles.navigation} aria-label="Chức năng chính">
    <div className={styles.tabs}>
      {tabs.map(({ to, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          end={to === ROUTES.HOME}
          className={({ isActive }) => `${styles.tab} ${isActive ? styles.active : ''}`}
        >
          <Icon size={19} aria-hidden="true" />
          <span>{ROUTE_LABELS[to]}</span>
        </NavLink>
      ))}
    </div>
  </nav>
);
