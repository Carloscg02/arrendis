import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../components/AuthProvider";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import ArrendisLogo from "../components/ArrendisLogo";

export default function Landing() {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="landing-page">
      {/* Top Editorial Navigation */}
      <header className="landing-nav">
        <div className="landing-nav__container">
          <Link to="/" className="landing-nav__brand">
            <ArrendisLogo size="sm" showSubtitle={false} />
          </Link>

          <nav className="landing-nav__links">
            <a href="#filosofia" className="landing-nav__link">Filosofía</a>
            <a href="#suministros" className="landing-nav__link">Suministros</a>
            <a href="#fiscalidad" className="landing-nav__link">Fiscalidad</a>
            <a href="#catalogo" className="landing-nav__link">Cartera</a>
          </nav>

          <div className="landing-nav__actions">
            {user ? (
              <button
                className="btn btn-primary btn-sm"
                onClick={() => navigate("/portfolio")}
              >
                <span>Ir a mi Cartera</span>
                <ArrowRight size={13} style={{ marginLeft: "0.35rem" }} />
              </button>
            ) : (
              <>
                <Link to="/login" className="landing-nav__link-btn">
                  Acceso
                </Link>
                <Link to="/register" className="btn btn-primary btn-sm">
                  Comenzar
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="landing-hero">
        <div className="landing-container">
          <div className="landing-hero__meta">
            <span className="mono-eyebrow">REGISTRO EDITORIAL &amp; GESTIÓN FISCAL ESPAÑOLA</span>
          </div>

          <h1 className="landing-hero__title">
            El arte de gestionar tu patrimonio inmobiliario con calma y rigor.
          </h1>

          <p className="landing-hero__subtitle">
            Una plataforma de alta precisión concebida para propietarios e inversores que entienden sus viviendas como arquitectura y patrimonio vivo. Automatización de suministros por CUPS, optimización fiscal en el IRPF y control sereno de contratos según la LAU.
          </p>

          <div className="landing-hero__cta">
            {user ? (
              <button
                className="btn btn-primary"
                onClick={() => navigate("/portfolio")}
              >
                <span>Abrir mi Cartera</span>
                <ArrowRight size={15} style={{ marginLeft: "0.45rem" }} />
              </button>
            ) : (
              <>
                <Link to="/register" className="btn btn-primary">
                  <span>Registrar Primer Inmueble</span>
                  <ArrowRight size={15} style={{ marginLeft: "0.45rem" }} />
                </Link>
                <Link to="/login" className="btn btn-secondary">
                  Acceso a Propietarios
                </Link>
              </>
            )}
          </div>

          {/* Hero Photography Frame (Imagen 1) */}
          <div className="landing-hero__frame">
            <div className="landing-image-wrapper">
              <img
                src="/images/editorial/hero-facade.jpg"
                alt="Arquitectura residencial histórica en Madrid Chamberí"
                className="landing-hero__img"
              />
            </div>
            <div className="landing-image-caption">
              <span className="mono-caption">FIG. 01 / FACHADA RESIDENCIAL HISTÓRICA · MADRID SEÑORIAL</span>
              <span className="mono-caption text-muted">PORTAFOLIO PATRIMONIAL ARRENDIS</span>
            </div>
          </div>
        </div>
      </section>

      {/* Manifesto / Core Values Strip */}
      <section className="landing-strip" id="filosofia">
        <div className="landing-container">
          <div className="landing-strip__grid">
            <div className="landing-strip__item">
              <span className="landing-strip__num">01</span>
              <h3 className="landing-strip__title">Rigor Fiscal Inquebrantable</h3>
              <p className="landing-strip__text">
                Cálculo automático de la amortización del 3% sobre el mayor valor y deducción de gastos conforme al Modelo 100 del IRPF.
              </p>
            </div>
            <div className="landing-strip__item">
              <span className="landing-strip__num">02</span>
              <h3 className="landing-strip__title">Automatización Silenciosa</h3>
              <p className="landing-strip__text">
                Vincula el código CUPS de luz, agua y gas. Las facturas recibidas por correo se asignan y computan sin intervención manual.
              </p>
            </div>
            <div className="landing-strip__item">
              <span className="landing-strip__num">03</span>
              <h3 className="landing-strip__title">Protección Legal LAU</h3>
              <p className="landing-strip__text">
                Seguimiento exhaustivo de fechas de vigencia, prórrogas obligatorias, fianzas y rentabilidades netas por inmueble.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Section 1: Architecture & Interior Comfort (Imagen 2) */}
      <section className="landing-feature">
        <div className="landing-container">
          <div className="landing-feature__grid">
            <div className="landing-feature__content">
              <span className="mono-eyebrow">CURADURÍA DEL INMUEBLE</span>
              <h2 className="landing-feature__title">
                Cada propiedad es un activo vivo, no una simple celda de cálculo.
              </h2>
              <p className="landing-feature__text">
                Arrendis organiza tu patrimonio con la sobriedad y el espacio que merece. Guarda fotografías de alta resolución, contratos firmados, datos catastrales e inventarios en un libro mayor digital sin ruido publicitario ni paneles innecesarios.
              </p>
              <div className="landing-feature__bullets">
                <div className="landing-bullet">
                  <CheckCircle2 size={16} className="text-garnet" />
                  <span>Ficha arquitectónica con dirección catastral y año de adquisición.</span>
                </div>
                <div className="landing-bullet">
                  <CheckCircle2 size={16} className="text-garnet" />
                  <span>Control de ocupación en tiempo real y rentabilidades anuales consolidadas.</span>
                </div>
                <div className="landing-bullet">
                  <CheckCircle2 size={16} className="text-garnet" />
                  <span>Historial unificado de incidencias y mantenimiento.</span>
                </div>
              </div>
            </div>

            <div className="landing-feature__visual">
              <div className="landing-image-wrapper">
                <img
                  src="/images/editorial/interior-comfort.jpg"
                  alt="Espacio interior rehabilitado con luz natural y suelos de roble"
                  className="landing-feature__img"
                />
              </div>
              <div className="landing-image-caption">
                <span className="mono-caption">FIG. 02 / REHABILITACIÓN INTERIOR · SUELOS DE ROBLE Y LUZ CENITAL</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section 2: Technical Atelier & Supplies Automation (Imagen 3) */}
      <section className="landing-feature landing-feature--reverse" id="suministros">
        <div className="landing-container">
          <div className="landing-feature__grid">
            <div className="landing-feature__visual">
              <div className="landing-image-wrapper">
                <img
                  src="/images/editorial/atelier-supplies.jpg"
                  alt="Mesa de trabajo de taller arquitectónico con plano y llaves"
                  className="landing-feature__img"
                />
              </div>
              <div className="landing-image-caption">
                <span className="mono-caption">FIG. 03 / TALLER DE GESTIÓN · ASIGNACIÓN DIRECTA POR CONTADOR</span>
              </div>
            </div>

            <div className="landing-feature__content">
              <span className="mono-eyebrow">TECNOLOGÍA DE PRECISIÓN</span>
              <h2 className="landing-feature__title">
                Facturas de suministros que se contabilizan solas.
              </h2>
              <p className="landing-feature__text">
                Olvida descargar PDFs mes a mes y transcribir consumos. Arrendis empareja cada factura eléctrica, de gas o de agua directamente con el CUPS de la vivienda correspondiente mediante extracción documental con inteligencia artificial.
              </p>
              <div className="landing-feature__steps">
                <div className="landing-step">
                  <span className="landing-step__num">01</span>
                  <div>
                    <strong>Asignación por CUPS</strong>
                    <p>Guarda el código de contador del piso una única vez.</p>
                  </div>
                </div>
                <div className="landing-step">
                  <span className="landing-step__num">02</span>
                  <div>
                    <strong>Buzón de Reenvío Privado</strong>
                    <p>Reenvía las facturas de Iberdrola, Endesa o Naturgy a tu correo privado de Arrendis.</p>
                  </div>
                </div>
                <div className="landing-step">
                  <span className="landing-step__num">03</span>
                  <div>
                    <strong>Cálculo Inmediato de Gasto</strong>
                    <p>El importe, IVA y fecha quedan vinculados al informe fiscal del inmueble.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section 3: Portfolio Showcase (Imagen 4 Opción 1) */}
      <section className="landing-showcase" id="catalogo">
        <div className="landing-container">
          <div className="landing-showcase__header">
            <span className="mono-eyebrow">FICHA DE CARTERA MODELO</span>
            <h2 className="landing-showcase__title">Una visión serena de tus activos.</h2>
            <p className="landing-showcase__subtitle">
              Así luce un inmueble gestionado con la disciplina de Arrendis: fotografía serena, métricas tabulares exactas y estado contractual al instante.
            </p>
          </div>

          <div className="landing-showcase__card">
            <div className="landing-showcase__img-box">
              <img
                src="/images/editorial/property-showcase-1.jpg"
                alt="Ficha de vivienda en edificio histórico residencial"
                className="landing-showcase__img"
              />
            </div>
            <div className="landing-showcase__info">
              <div className="landing-showcase__top">
                <span className="badge badge-garnet">ALQUILADO</span>
                <span className="mono-caption">REF: MAD-CH-04</span>
              </div>
              <h3 className="landing-showcase__name">Vivienda Señorial Chamberí</h3>
              <p className="landing-showcase__address">Calle de Zurbano 42, Madrid · 145 m²</p>

              <div className="landing-showcase__metrics">
                <div className="landing-metric">
                  <span className="landing-metric__label">RENTA MENSUAL</span>
                  <span className="landing-metric__value">1.850,00 €</span>
                </div>
                <div className="landing-metric">
                  <span className="landing-metric__label">RENDIMIENTO NETO ESTIMADO</span>
                  <span className="landing-metric__value text-garnet">1.520,40 €</span>
                </div>
                <div className="landing-metric">
                  <span className="landing-metric__label">AMORTIZACIÓN DEDUCIBLE ANUAL</span>
                  <span className="landing-metric__value">5.820,00 €</span>
                </div>
              </div>

              <div className="landing-showcase__action">
                <Link to="/register" className="btn btn-primary btn-sm">
                  <span>Comenzar con tu Propiedad</span>
                  <ArrowRight size={13} style={{ marginLeft: "0.35rem" }} />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Final Call to Action */}
      <section className="landing-cta" id="fiscalidad">
        <div className="landing-container">
          <div className="landing-cta__box">
            <span className="mono-eyebrow text-garnet">ARRENDIS ATELIER PATRIMONIAL</span>
            <h2 className="landing-cta__title">
              Paz mental para tu patrimonio inmobiliario en España.
            </h2>
            <p className="landing-cta__text">
              Comienza hoy mismo a registrar tus inmuebles, adjuntar contratos y automatizar tus facturas de suministros.
            </p>
            <div className="landing-cta__buttons">
              {user ? (
                <button
                  className="btn btn-primary btn-lg"
                  onClick={() => navigate("/portfolio")}
                >
                  <span>Acceder a mi Cartera</span>
                  <ArrowRight size={16} style={{ marginLeft: "0.45rem" }} />
                </button>
              ) : (
                <>
                  <Link to="/register" className="btn btn-primary btn-lg">
                    <span>Crear Cuenta Gratuita</span>
                    <ArrowRight size={16} style={{ marginLeft: "0.45rem" }} />
                  </Link>
                  <Link to="/login" className="btn btn-secondary btn-lg">
                    Iniciar Sesión
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Editorial Footer */}
      <footer className="landing-footer">
        <div className="landing-container">
          <div className="landing-footer__grid">
            <div className="landing-footer__brand-col">
              <div style={{ marginBottom: "1.25rem" }}>
                <ArrendisLogo size="md" showSubtitle={true} />
              </div>
              <p className="landing-footer__desc">
                Registro patrimonial y fiscal de inmuebles en alquiler en España. Diseñado con rigor legal y calma arquitectónica.
              </p>
            </div>

            <div className="landing-footer__col">
              <span className="mono-eyebrow">SISTEMA</span>
              <ul className="landing-footer__links">
                <li><a href="#filosofia">Filosofía</a></li>
                <li><a href="#suministros">Automatización CUPS</a></li>
                <li><a href="#fiscalidad">Cálculo IRPF</a></li>
                <li><Link to="/portfolio">Cartera Digital</Link></li>
              </ul>
            </div>

            <div className="landing-footer__col">
              <span className="mono-eyebrow">LEGAL &amp; FISCAL</span>
              <ul className="landing-footer__links">
                <li><span>Ley de Arrendamientos Urbanos (LAU)</span></li>
                <li><span>Normativa IRPF Agencia Tributaria</span></li>
                <li><span>Modelo 100 AEAT</span></li>
                <li><span>Privacidad y Cifrado</span></li>
              </ul>
            </div>
          </div>

          <div className="landing-footer__bottom">
            <span className="mono-caption">
              © {new Date().getFullYear()} ARRENDIS PATRIMONIAL S.L. · TODOS LOS DERECHOS RESERVADOS.
            </span>
            <span className="mono-caption text-muted">
              DISEÑADO CON RIGOR EDITORIAL Y CALMA ARQUITECTÓNICA.
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
