import { Share2, PlusSquare, CheckCircle2, X, Smartphone } from 'lucide-react';

interface PWAInstallModalIOSProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function PWAInstallModalIOS({ isOpen, onClose }: PWAInstallModalIOSProps) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="ios-modal-title">
      <div className="modal-backdrop" role="button" tabIndex={-1} onClick={onClose} onKeyDown={(e) => e.key === 'Escape' && onClose()} />
      <div className="pwa-ios-modal">
        <header className="pwa-ios-modal__header">
          <div className="pwa-ios-modal__title-row">
            <div className="pwa-ios-modal__icon-badge" aria-hidden="true">
              <Smartphone size={18} strokeWidth={1.75} />
            </div>
            <h2 id="ios-modal-title" className="pwa-ios-modal__title">
              Instalar en tu iPhone o iPad
            </h2>
          </div>
          <button
            type="button"
            className="pwa-ios-modal__close-btn touch-target-compact"
            onClick={onClose}
            aria-label="Cerrar guía de instalación"
          >
            <X size={18} strokeWidth={2} />
          </button>
        </header>

        <div className="pwa-ios-modal__body">
          <p className="pwa-ios-modal__subtitle">
            Añade Arrendis a tu pantalla de inicio para una experiencia a pantalla completa sin barras de navegador:
          </p>

          <ol className="pwa-ios-steps">
            <li className="pwa-ios-step">
              <div className="pwa-ios-step__icon" aria-hidden="true">
                <Share2 size={16} strokeWidth={2} />
              </div>
              <div className="pwa-ios-step__content">
                <strong>1. Pulsa Compartir</strong>
                <span>Toca el icono de Compartir en la barra de navegación de Safari (abajo en iPhone, arriba en iPad).</span>
              </div>
            </li>

            <li className="pwa-ios-step">
              <div className="pwa-ios-step__icon" aria-hidden="true">
                <PlusSquare size={16} strokeWidth={2} />
              </div>
              <div className="pwa-ios-step__content">
                <strong>2. Añadir a pantalla de inicio</strong>
                <span>Desplaza la lista de opciones y selecciona «Añadir a pantalla de inicio».</span>
              </div>
            </li>

            <li className="pwa-ios-step">
              <div className="pwa-ios-step__icon" aria-hidden="true">
                <CheckCircle2 size={16} strokeWidth={2} />
              </div>
              <div className="pwa-ios-step__content">
                <strong>3. Confirmar</strong>
                <span>Pulsa «Añadir» en la esquina superior derecha. El icono de Arrendis aparecerá en tu escritorio.</span>
              </div>
            </li>
          </ol>
        </div>

        <footer className="pwa-ios-modal__footer">
          <button
            type="button"
            className="btn btn-primary pwa-ios-modal__confirm-btn touch-target"
            onClick={onClose}
          >
            Entendido
          </button>
        </footer>
      </div>
    </div>
  );
}
