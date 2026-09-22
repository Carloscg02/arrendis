import { Routes, Route } from 'react-router-dom';
import PropertyList from './pages/PropertyList';
import PropertyDetail from './pages/PropertyDetail';
import Login from './pages/Login';
import Register from './pages/Register';
import Landing from './pages/Landing';
import ProtectedRoute from './components/ProtectedRoute';
import PublicOnlyRoute from './components/PublicOnlyRoute';
import AppHeader from './components/AppHeader';
import { AuthProvider, useAuth } from './components/AuthProvider';
import { ErrorBoundary } from './components/ErrorBoundary';

function HomeRoute() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <ProtectedRoute>
        <AppHeader />
        <PropertyList />
      </ProtectedRoute>
    );
  }

  return <Landing />;
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Routes>
          {/* Inicio inteligente: si autenticado -> Cartera; si no -> Landing */}
          <Route path="/" element={<HomeRoute />} />
          
          {/* Acceso directo a la landing page pública */}
          <Route path="/landing" element={<Landing />} />

          {/* Cartera de Inmuebles */}
          <Route path="/portfolio" element={
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
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
