import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../components/AuthProvider';
import { useToast } from '../components/Toast';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import ArrendisLogo from '../components/ArrendisLogo';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const { error, success } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login({ email, password });
      success('Inicio de sesión exitoso');
      navigate('/');
    } catch (err: any) {
      error(err.message || 'Error al iniciar sesión');
    }
  };

  return (
    <div className="auth-split-layout">
      {/* Left Column: Architectural Visual Monograph */}
      <div className="auth-split-visual">
        <img
          src="/images/editorial/hero-facade.jpg"
          alt="Arquitectura residencial histórica en Madrid"
          className="auth-split-visual__bg"
        />
        <div className="auth-split-visual__overlay" />

        <div className="auth-split-visual__top">
          <span className="mono-eyebrow" style={{ color: 'rgba(249, 247, 245, 0.75)' }}>
            ARRENDIS · ATELIER PATRIMONIAL
          </span>
        </div>

        <div className="auth-split-visual__bottom">
          <blockquote className="auth-split-visual__quote">
            “La calma de saber que cada contrato, suministro y deducción fiscal está en su lugar exacto.”
          </blockquote>
          <span className="auth-split-visual__author">
            FIG. AUTH · CUADERNO DE BITÁCORA RESIDENCIAL · MADRID
          </span>
        </div>
      </div>

      {/* Right Column: Editorial Atelier Form */}
      <div className="auth-split-form-panel">
        <div className="auth-split-form-header">
          <Link to="/" className="auth-split-back-link">
            <ArrowLeft size={13} />
            <span>Volver a la portada</span>
          </Link>
        </div>

        <div className="auth-split-form-content">
          <div style={{ marginBottom: '1.75rem' }}>
            <ArrendisLogo size="md" showSubtitle={true} />
          </div>

          <h1 className="auth-split-title">Acceso a Propietarios</h1>
          <p className="auth-split-subtitle">
            Introduzca sus credenciales para consultar y operar su cartera inmobiliaria.
          </p>

          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="login-email">CORREO ELECTRÓNICO</label>
              <input
                id="login-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="propietario@arrendis.com"
                required
                autoComplete="email"
              />
            </div>

            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.45rem' }}>
                <label htmlFor="login-password" style={{ margin: 0 }}>CONTRASEÑA</label>
              </div>
              <input
                id="login-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                required
                autoComplete="current-password"
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ marginTop: '0.75rem' }}>
              <span>Entrar a mi Cartera</span>
              <ArrowRight size={14} style={{ marginLeft: '0.4rem' }} />
            </button>
          </form>

          <div className="auth-link">
            ¿Aún no tiene cuenta registrada?{' '}
            <Link to="/register">Cree su cuenta aquí</Link>
          </div>
        </div>

        <div className="auth-split-footer">
          <span>© {new Date().getFullYear()} ARRENDIS · CIFRADO &amp; RIGOR FISCAL ESPAÑOL</span>
        </div>
      </div>
    </div>
  );
}
