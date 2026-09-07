import { Routes, Route } from 'react-router-dom';
import PropertyList from './pages/PropertyList';
import PropertyDetail from './pages/PropertyDetail';
import Login from './pages/Login';
import Register from './pages/Register';
import ProtectedRoute from './components/ProtectedRoute';
import PublicOnlyRoute from './components/PublicOnlyRoute';
import AppHeader from './components/AppHeader';
import { AuthProvider } from './components/AuthProvider';
import { ErrorBoundary } from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Routes>
        {/* Rutas protegidas */}
        <Route path="/" element={
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

        {/* Rutas públicas */}
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
