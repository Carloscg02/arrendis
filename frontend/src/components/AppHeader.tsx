
import { Link } from 'react-router-dom';
import { User as UserIcon } from 'lucide-react';
import { useAuth } from './AuthProvider';
import ArrendisLogo from './ArrendisLogo';

export default function AppHeader() {
  const { user, logout } = useAuth();

  return (
    <header className="app-header">
      <div className="app-header__container">
        <Link to="/" className="app-header__brand" title="Arrendis — Gestión Patrimonial">
          <ArrendisLogo size="sm" showSubtitle={false} />
        </Link>
        {user && (
          <div className="app-header__user">
            <div className="app-header__user-info">
              <div className="app-header__avatar" aria-hidden="true">
                <UserIcon size={14} strokeWidth={1.75} />
              </div>
              <span className="app-header__username">{user.username}</span>
            </div>
            <button className="btn btn-secondary app-header__logout-btn" onClick={logout}>
              Cerrar Sesión
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
