import { useState, useEffect } from 'react';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export function usePWAInstall() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isStandalone, setIsStandalone] = useState<boolean>(false);
  const [isIOS, setIsIOS] = useState<boolean>(false);
  const [isDismissed, setIsDismissed] = useState<boolean>(true);

  useEffect(() => {
    // 1. Detectar si ya se ejecuta como PWA instalada (Standalone Mode)
    const inStandalone =
      window.matchMedia('(display-mode: standalone)').matches ||
      (window.navigator as unknown as { standalone?: boolean }).standalone === true;
    setIsStandalone(inStandalone);

    // 2. Detectar si es un navegador iOS / iPadOS
    const ua = window.navigator.userAgent.toLowerCase();
    const isAppleDevice = /iphone|ipad|ipod/.test(ua) || (ua.includes('mac') && window.navigator.maxTouchPoints > 1);
    setIsIOS(isAppleDevice);

    // 3. Comprobar período de cortesía (cooldown) en localStorage
    const dismissedUntil = localStorage.getItem('arrendis_pwa_dismissed_until');
    const now = Date.now();
    if (dismissedUntil && now < parseInt(dismissedUntil, 10)) {
      setIsDismissed(true);
    } else {
      setIsDismissed(false);
    }

    // 4. Interceptar evento beforeinstallprompt en Chromium/Android
    const handleBeforeInstall = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstall);
    return () => window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
  }, []);

  const triggerInstall = async () => {
    if (deferredPrompt) {
      await deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      if (outcome === 'accepted') {
        setDeferredPrompt(null);
      }
    }
  };

  const dismissPrompt = (days = 14) => {
    const expireTime = Date.now() + days * 24 * 60 * 60 * 1000;
    localStorage.setItem('arrendis_pwa_dismissed_until', expireTime.toString());
    setIsDismissed(true);
  };

  // Solo mostrar en navegadores que no están en standalone, no en cooldown,
  // y que soportan prompt directo (Android) o son iOS que requiere guía
  const canInstall = !isStandalone && !isDismissed && (Boolean(deferredPrompt) || isIOS);

  return {
    canInstall,
    isStandalone,
    isIOS,
    canPromptDirectly: Boolean(deferredPrompt),
    triggerInstall,
    dismissPrompt,
  };
}
