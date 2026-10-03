import { Link, useLocation } from 'react-router-dom';
import { ArrowLeft, Home, Compass } from 'lucide-react';
import ArrendisLogo from '../components/ArrendisLogo';

export default function NotFound() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] antialiased flex flex-col justify-between">
      {/* Top Editorial Header */}
      <header className="border-b border-[var(--panel-border)] bg-[var(--bg-secondary)] px-4 py-4 sm:px-8">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors min-h-[44px] min-w-[44px]"
          >
            <ArrowLeft size={16} />
            <span>Volver al Inicio</span>
          </Link>
          <ArrendisLogo size="sm" showSubtitle={false} />
        </div>
      </header>

      {/* Main Content Area */}
      <main className="mx-auto max-w-2xl px-4 py-16 text-center">
        <span className="font-mono text-xs text-[var(--brand-burgundy)] tracking-widest uppercase block mb-3 font-semibold">
          404 · Error de Navegación
        </span>
        <h1 className="font-serif text-4xl sm:text-5xl text-[var(--text-primary)] font-medium mb-4 tracking-tight">
          Página no encontrada
        </h1>
        <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-6 max-w-lg mx-auto">
          La dirección que ha solicitado no existe, ha sido trasladada o el enlace
          utilizado contiene una errata. Su cartera e información fiscal permanecen
          plenamente seguras.
        </p>

        <div className="bg-[var(--bg-secondary)] border border-[var(--panel-border)] p-3 rounded-sm font-mono text-xs text-[var(--text-muted)] mb-8 inline-block max-w-full truncate">
          Ruta intentada: <code className="text-[var(--text-primary)]">{location.pathname}</code>
        </div>

        <div className="flex flex-col sm:flex-row justify-center items-center gap-4">
          <Link
            to="/"
            className="btn btn-primary btn-sm flex items-center justify-center gap-2 min-h-[44px] min-w-[140px] w-full sm:w-auto"
          >
            <Home size={15} />
            <span>Página Principal</span>
          </Link>
          <Link
            to="/portfolio"
            className="btn btn-secondary btn-sm flex items-center justify-center gap-2 min-h-[44px] min-w-[140px] w-full sm:w-auto"
          >
            <Compass size={15} />
            <span>Mi Cartera</span>
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--panel-border)] py-6 text-center text-xs font-mono text-[var(--text-muted)]">
        © 2026 Arrendis · Atelier Editorial · Sistema de Resiliencia de Navegación
      </footer>
    </div>
  );
}
