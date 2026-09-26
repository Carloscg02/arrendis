import { useState } from 'react';
import { Smartphone, X, Download } from 'lucide-react';
import { usePWAInstall } from '../utils/usePWAInstall';
import PWAInstallModalIOS from './PWAInstallModalIOS';

export default function PWAInstallBanner() {
  const { canInstall, isIOS, canPromptDirectly, triggerInstall, dismissPrompt } = usePWAInstall();
  const [showIOSModal, setShowIOSModal] = useState<boolean>(false);

  if (!canInstall) {
    return null;
  }

  const handleActionClick = () => {
    if (isIOS) {
      setShowIOSModal(true);
    } else if (canPromptDirectly) {
      triggerInstall();
    }
  };

  return (
    <>
      <aside className="pwa-banner" aria-label="Instalación de aplicación móvil">
        <div className="pwa-banner__container">
          <div className="pwa-banner__info">
            <div className="pwa-banner__icon" aria-hidden="true">
              <Smartphone size={16} strokeWidth={1.75} />
            </div>
            <div className="pwa-banner__text">
              <span className="pwa-banner__title">Instalar Arrendis en tu móvil</span>
              <span className="pwa-banner__desc">Acceso instantáneo y pantalla completa sin tiendas de aplicaciones.</span>
            </div>
          </div>

          <div className="pwa-banner__actions">
            <button
              type="button"
              className="pwa-banner__dismiss-btn touch-target-compact"
              onClick={() => dismissPrompt(14)}
            >
              Ahora no
            </button>
            <button
              type="button"
              className="btn btn-primary pwa-banner__install-btn touch-target-compact"
              onClick={handleActionClick}
            >
              <Download size={14} strokeWidth={2} style={{ marginRight: '0.4rem' }} aria-hidden="true" />
              {isIOS ? 'Cómo instalar' : 'Instalar app'}
            </button>
            <button
              type="button"
              className="pwa-banner__close-icon touch-target-compact"
              onClick={() => dismissPrompt(14)}
              aria-label="Cerrar aviso de instalación"
            >
              <X size={15} strokeWidth={2} />
            </button>
          </div>
        </div>
      </aside>

      {isIOS && (
        <PWAInstallModalIOS
          isOpen={showIOSModal}
          onClose={() => setShowIOSModal(false)}
        />
      )}
    </>
  );
}
