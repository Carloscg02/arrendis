
import { Link } from 'react-router-dom';
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
              <div className="app-header__avatar">
                {user.username.charAt(0).toUpperCase()}
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
