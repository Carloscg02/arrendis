import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.arrendis.app',
  appName: 'Arrendis',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
    // En producción se fuerza HTTPS seguro; en desarrollo local permite cleartext si se define la variable
    cleartext: process.env.CAPACITOR_CLEARTEXT === 'true',
  },
  android: {
    allowMixedContent: false,
    captureInput: true,
    webContentsDebuggingEnabled: false,
  },
};

export default config;
