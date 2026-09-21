import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../components/AuthProvider';
import { useToast } from '../components/Toast';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import ArrendisLogo from '../components/ArrendisLogo';

export default function Register() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const { register } = useAuth();
  const { error, success } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      error('Las contraseñas no coinciden');
      return;
    }
    try {
      await register({ email, username, password });
      success('Cuenta creada exitosamente');
      navigate('/');
    } catch (err: any) {
      error(err.message || 'Error al registrar');
    }
  };

  return (
    <div className="auth-split-layout">
      {/* Left Column: Architectural Interior Plate */}
      <div className="auth-split-visual">
        <img
          src="/images/editorial/interior-comfort.jpg"
          alt="Espacio interior rehabilitado con luz natural"
          className="auth-split-visual__bg"
        />
        <div className="auth-split-visual__overlay" />

        <div className="auth-split-visual__top">
          <span className="mono-eyebrow" style={{ color: 'rgba(249, 247, 245, 0.75)' }}>
            ARRENDIS · ALTA EN EL REGISTRO
          </span>
        </div>

        <div className="auth-split-visual__bottom">
          <blockquote className="auth-split-visual__quote">
            “Incorpore su patrimonio a un libro mayor digital concebido para perdurar con calma y rigor.”
          </blockquote>
          <span className="auth-split-visual__author">
            FIG. REG · GESTIÓN PATRIMONIAL CONFORME A LA LEY
          </span>
        </div>
      </div>

      {/* Right Column: Editorial Registration Form */}
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

          <h1 className="auth-split-title">Crear Cuenta</h1>
          <p className="auth-split-subtitle">
            Comience a gestionar sus inmuebles en alquiler con tranquilidad fiscal y automatización documental.
          </p>

          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="reg-email">CORREO ELECTRÓNICO</label>
              <input
                id="reg-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="propietario@arrendis.com"
                required
                autoComplete="email"
              />
            </div>

            <div className="form-group">
              <label htmlFor="reg-user">NOMBRE O TITULAR</label>
              <input
                id="reg-user"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Carlos González"
                required
                autoComplete="name"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="reg-pass">CONTRASEÑA</label>
                <input
                  id="reg-pass"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  autoComplete="new-password"
                />
              </div>

              <div className="form-group">
                <label htmlFor="reg-confirm">CONFIRMAR</label>
                <input
                  id="reg-confirm"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  autoComplete="new-password"
                />
              </div>
            </div>

            <button type="submit" className="btn btn-primary" style={{ marginTop: '0.75rem' }}>
              <span>Registrar Cuaderno Patrimonial</span>
              <ArrowRight size={14} style={{ marginLeft: '0.4rem' }} />
            </button>
          </form>

          <div className="auth-link">
            ¿Ya tiene una cuenta de propietario?{' '}
            <Link to="/login">Inicie sesión aquí</Link>
          </div>
        </div>

        <div className="auth-split-footer">
          <span>© {new Date().getFullYear()} ARRENDIS · PROTECCIÓN DE DATOS &amp; PRIVACIDAD PATRIMONIAL</span>
        </div>
      </div>
    </div>
  );
}
