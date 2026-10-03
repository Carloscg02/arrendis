import { Routes, Route } from 'react-router-dom';
import PropertyList from './pages/PropertyList';
import PropertyDetail from './pages/PropertyDetail';
import Login from './pages/Login';
import Register from './pages/Register';
import Landing from './pages/Landing';
import PrivacyPolicy from './pages/PrivacyPolicy';
import TermsOfService from './pages/TermsOfService';
import Onboarding from './pages/Onboarding';
import ProtectedRoute from './components/ProtectedRoute';
import PublicOnlyRoute from './components/PublicOnlyRoute';
import AppHeader from './components/AppHeader';
import PWAInstallBanner from './components/PWAInstallBanner';
import { AuthProvider, useAuth } from './components/AuthProvider';
import { ErrorBoundary } from './components/ErrorBoundary';

function HomeRoute() {
  const { isAuthenticated, loading, user } = useAuth();

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    if (user && user.onboarding_completed === false) {
      return (
        <ProtectedRoute>
          <Onboarding />
        </ProtectedRoute>
      );
    }

    return (
      <ProtectedRoute>
        <AppHeader />
        <PropertyList />
      </ProtectedRoute>
    );
  }

  // Si la app se ejecuta instalada en modo standalone (PWA o APK/Capacitor en móvil),
  // se omite la landing comercial y se dirige de inmediato al Login / Cartera.
  const isStandalone = typeof window !== 'undefined' && (
    window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as any).standalone === true ||
    document.referrer.includes('android-app://')
  );

  if (isStandalone) {
    return (
      <PublicOnlyRoute>
        <Login />
      </PublicOnlyRoute>
    );
  }

  return <Landing />;
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Routes>
          {/* Inicio inteligente: si autenticado -> Cartera o Onboarding; si no -> Landing */}
          <Route path="/" element={<HomeRoute />} />
          
          {/* Acceso directo a la landing page pública */}
          <Route path="/landing" element={<Landing />} />

          {/* Rutas legales públicas (F-41) */}
          <Route path="/privacy" element={<PrivacyPolicy />} />
          <Route path="/terms" element={<TermsOfService />} />

          {/* Onboarding guiado */}
          <Route path="/onboarding" element={
            <ProtectedRoute>
              <Onboarding />
            </ProtectedRoute>
          } />

          {/* Cartera de Inmuebles */}
          <Route path="/portfolio" element={
            <ProtectedRoute>
              <AppHeader />
              <PropertyList />
            </ProtectedRoute>
          } />

          <Route path="/properties" element={
            <ProtectedRoute>
              <AppHeader />
              <PropertyList />
            </ProtectedRoute>
          } />

          <Route path="/properties/:id" element={
            <ProtectedRoute>
              <AppHeader />
              <PropertyDetail />
            </ProtectedRoute>
          } />

          {/* Rutas públicas de autenticación */}
          <Route path="/login" element={
            <PublicOnlyRoute>
              <Login />
            </PublicOnlyRoute>
          } />
          <Route path="/register" element={
            <PublicOnlyRoute>
              <Register />
            </PublicOnlyRoute>
          } />
        </Routes>
        <PWAInstallBanner />
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
