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
            <span className="mono-eyebrow">GESTIÓN DE INMUEBLES &amp; CÁLCULO FISCAL</span>
          </div>

          <h1 className="landing-hero__title">
            Gestiona tus alquileres con claridad.
          </h1>

          <p className="landing-hero__subtitle">
            Una aplicación práctica pensada para propietarios. Centraliza tus contratos e inquilinos, automatiza el registro de las facturas de suministros por propiedad y obtén el cálculo de tu fiscalidad organizado según el Modelo 100 oficial de la Agencia Tributaria (AEAT).
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
                  Iniciar Sesión
                </Link>
              </>
            )}
          </div>

          {/* Hero Photography Frame (Imagen 1) */}
          <div className="landing-hero__frame">
            <div className="landing-image-wrapper">
              <img
                src="/images/editorial/hero-facade.jpg"
                alt="Arquitectura residencial en Madrid"
                className="landing-hero__img"
              />
            </div>
            <div className="landing-image-caption">
              <span className="mono-caption">GESTIÓN DE ALQUILERES CON ARRENDIS</span>
              <span className="mono-caption text-muted"></span>
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
              <h3 className="landing-strip__title">Cálculo para el IRPF</h3>
              <p className="landing-strip__text">
                Calcula la amortización deducible del 3% y organiza los gastos de cada vivienda listos para consultar en tu declaración.
              </p>
            </div>
            <div className="landing-strip__item">
              <span className="landing-strip__num">02</span>
              <h3 className="landing-strip__title">Facturas por CUPS</h3>
              <p className="landing-strip__text">
                Vincula el código de contador de cada piso. Reenvía las facturas de luz, gas o agua y se asociarán a su inmueble automáticamente.
              </p>
            </div>
            <div className="landing-strip__item">
              <span className="landing-strip__num">03</span>
              <h3 className="landing-strip__title">Control de Inquilinos y Rentas</h3>
              <p className="landing-strip__text">
                Ten a mano las fechas de contrato, el importe de la renta, las fianzas y los ingresos netos de cada propiedad sin perder papeles.
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
              <span className="mono-eyebrow">FICHA DE LA VIVIENDA</span>
              <h2 className="landing-feature__title">
                Toda la información de cada piso en un único lugar.
              </h2>
              <p className="landing-feature__text">
                Olvídate de buscar contratos y números en carpetas dispersas. Arrendis reúne los datos catastrales, contratos, fotos y notas de cada vivienda en una ficha ordenada y fácil de consultar.
              </p>
              <div className="landing-feature__bullets">
                <div className="landing-bullet">
                  <CheckCircle2 size={16} className="text-garnet" />
                  <span>Datos catastrales y valor de compra para el cálculo de amortización.</span>
                </div>
                <div className="landing-bullet">
                  <CheckCircle2 size={16} className="text-garnet" />
                  <span>Control de rentas mensuales y rendimiento estimado.</span>
                </div>
                <div className="landing-bullet">
                  <CheckCircle2 size={16} className="text-garnet" />
                  <span>Documentos y notas del inmueble siempre localizados.</span>
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
                <span className="mono-caption"></span>
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
                  alt="Facturas de suministros y llaves de inmueble"
                  className="landing-feature__img"
                />
              </div>
              <div className="landing-image-caption">
                <span className="mono-caption"></span>
              </div>
            </div>

            <div className="landing-feature__content">
              <span className="mono-eyebrow">AUTOMATIZACIÓN DE SUMINISTROS</span>
              <h2 className="landing-feature__title">
                Facturas de suministros que se contabilizan solas.
              </h2>
              <p className="landing-feature__text">
                Olvida descargar PDFs mes a mes y copiar números a mano. Arrendis lee tus facturas de luz, gas o agua, extrae los importes y las vincula directamente con el inmueble correspondiente mediante su código CUPS.
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
                    <strong>Buzón de Reenvío</strong>
                    <p>Reenvía las facturas de Iberdrola, Endesa o Naturgy a tu buzón de Arrendis.</p>
                  </div>
                </div>
                <div className="landing-step">
                  <span className="landing-step__num">03</span>
                  <div>
                    <strong>Cómputo Automático</strong>
                    <p>El importe y fecha se asignan a la vivienda y se suman al cálculo fiscal.</p>
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
            <span className="mono-eyebrow">VISTA DE INMUEBLE</span>
            <h2 className="landing-showcase__title">Una visión clara de cada alquiler.</h2>
            <p className="landing-showcase__subtitle">
              Así luce un inmueble gestionado con Arrendis: fotografía de la vivienda, datos clave del contrato y cálculo deducible en un solo vistazo.
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
            <span className="mono-eyebrow text-garnet">GESTIÓN CLARA Y DIRECTA</span>
            <h2 className="landing-cta__title">
              Pon orden en tus alquileres.
            </h2>
            <p className="landing-cta__text">
              Añade tus inmuebles, guarda tus contratos y deja que las facturas de suministros se asocien automáticamente.
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
                Gestión práctica de inmuebles en alquiler y cálculo estimativo para el IRPF. Creado para propietarios que buscan sencillez y orden.
              </p>
            </div>

            <div className="landing-footer__col">
              <span className="mono-eyebrow">SISTEMA</span>
              <ul className="landing-footer__links">
                <li><a href="#filosofia">Características</a></li>
                <li><a href="#suministros">Suministros por CUPS</a></li>
                <li><a href="#fiscalidad">Cálculo IRPF</a></li>
                <li><Link to="/portfolio">Mi Cartera</Link></li>
              </ul>
            </div>

            <div className="landing-footer__col">
              <span className="mono-eyebrow">FISCALIDAD &amp; AVISOS</span>
              <ul className="landing-footer__links">
                <li><span>Cálculo estimativo Modelo 100</span></li>
                <li><span>Amortización del 3% (Construcción)</span></li>
                <li><span>Gastos deducibles del alquiler</span></li>
                <li><span>Aviso: Herramienta de estimación</span></li>
              </ul>
            </div>
          </div>

          <div className="landing-footer__bottom">
            <span className="mono-caption">
              © {new Date().getFullYear()} ARRENDIS · GESTIÓN DE ALQUILERES Y CÁLCULO FISCAL.
            </span>
            <span className="mono-caption text-muted">
              HERRAMIENTA ESTIMATIVA DE APOYO AL PROPIETARIO.
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
