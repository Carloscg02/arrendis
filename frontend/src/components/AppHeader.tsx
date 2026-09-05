
import { Link } from 'react-router-dom';
import { Building2 } from 'lucide-react';
import { useAuth } from './AuthProvider';

export default function AppHeader() {
  const { user, logout } = useAuth();

  return (
    <header className="app-header">
      <div className="app-header__container">
        <Link to="/" className="app-header__logo">
          <span className="app-header__logo-icon">
            <Building2 size={18} />
          </span>
          <span className="app-header__logo-text">Rental Handler</span>
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
