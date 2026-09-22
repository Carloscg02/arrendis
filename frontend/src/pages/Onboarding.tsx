import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowRight, 
  ArrowLeft, 
  Check, 
  FileText, 
  Mail, 
  UploadCloud, 
  Zap,
  Info,
  BookOpen
} from 'lucide-react';
import ArrendisLogo from '../components/ArrendisLogo';
import { useAuth } from '../components/AuthProvider';
import { getQuickFiscalEstimate, bootstrapOnboarding, skipOnboarding } from '../services/api';
import type { QuickEstimateResponse } from '../types';
import { useToast } from '../components/Toast';

export default function Onboarding() {
  const navigate = useNavigate();
  const toast = useToast();
  const { markOnboardingCompleted } = useAuth();

  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [submitting, setSubmitting] = useState(false);
  const [skipping, setSkipping] = useState(false);

  // Paso 1: Inmueble
  const [propertyName, setPropertyName] = useState('');
  const [propertyType, setPropertyType] = useState('apartment');
  const [city, setCity] = useState('');
  const [street, setStreet] = useState('');

  // Paso 2: Fiscalidad
  const currentYear = new Date().getFullYear();
  const [purchasePrice, setPurchasePrice] = useState<number | ''>(210000);
  const [acquisitionYear, setAcquisitionYear] = useState<number | ''>(currentYear - 3);
  const [estimate, setEstimate] = useState<QuickEstimateResponse | null>(null);
  const [loadingEstimate, setLoadingEstimate] = useState(false);

  // Paso 3: Alquiler y Suministros
  const [monthlyRent, setMonthlyRent] = useState<number | ''>(950);
  const [cupsElectricity, setCupsElectricity] = useState('');
  const [skipCupsNotice, setSkipCupsNotice] = useState(false);

  // Simulación en tiempo real (debounced)
  useEffect(() => {
    if (!purchasePrice || purchasePrice <= 0 || !acquisitionYear) {
      setEstimate(null);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setLoadingEstimate(true);
        const res = await getQuickFiscalEstimate({
          purchase_price: Number(purchasePrice),
          acquisition_year: Number(acquisitionYear),
        });
        setEstimate(res);
      } catch (err) {
        console.error('Error calculando estimación fiscal:', err);
      } finally {
        setLoadingEstimate(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [purchasePrice, acquisitionYear]);

  // Manejador de omisión voluntaria
  const handleSkip = async () => {
    try {
      setSkipping(true);
      await skipOnboarding();
      markOnboardingCompleted();
      navigate('/portfolio');
    } catch (err: any) {
      toast.error(err.message || 'Error al omitir la guía.');
      markOnboardingCompleted();
      navigate('/portfolio');
    } finally {
      setSkipping(false);
    }
  };

  // Manejador del paso 1
  const handleNextStep1 = (e: React.FormEvent) => {
    e.preventDefault();
    if (!propertyName.trim()) {
      toast.error('Indica un nombre o alias para el inmueble.');
      return;
    }
    setStep(2);
  };

  // Manejador del paso 2
  const handleNextStep2 = () => {
    setStep(3);
  };

  // Finalización y bootstrap atómico
  const handleFinish = async () => {
    try {
      setSubmitting(true);
      const res = await bootstrapOnboarding({
        property_name: propertyName.trim(),
        property_type: propertyType,
        city: city.trim() || 'Ciudad',
        street: street.trim() || 'Dirección pendiente',
        purchase_price: purchasePrice ? Number(purchasePrice) : null,
        acquisition_year: acquisitionYear ? Number(acquisitionYear) : null,
        monthly_rent: monthlyRent ? Number(monthlyRent) : null,
        cups_electricity: cupsElectricity.trim() || null,
      });

      markOnboardingCompleted();
      toast.success('¡Patrimonio registrado con éxito! Tu estimación fiscal está activa.');
      navigate(`/properties/${res.id}?welcome=true`);
    } catch (err: any) {
      toast.error(err.message || 'Error al registrar tu propiedad.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--bg-primary, #f9f7f5)',
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Header superior limpio */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '1.25rem 2rem',
        borderBottom: '1px solid var(--panel-border, #e5e2dd)',
        backgroundColor: '#ffffff',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <ArrendisLogo size="sm" showSubtitle={true} />
        </div>

        {/* Indicador de pasos */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{
            fontSize: '0.75rem',
            fontFamily: 'var(--font-mono)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: 'var(--text-muted)',
          }}>
            Paso {step} de 3
          </span>
          <div style={{ display: 'flex', gap: '0.35rem' }}>
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                style={{
                  width: '28px',
                  height: '4px',
                  borderRadius: '2px',
                  backgroundColor: s <= step ? 'var(--brand-burgundy, #6b0008)' : 'var(--panel-border, #e5e2dd)',
                  transition: 'background-color 0.25s ease',
                }}
              />
            ))}
          </div>
        </div>

        {/* Botón de omitir */}
        <button
          onClick={handleSkip}
          disabled={skipping || submitting}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            fontSize: '0.85rem',
            cursor: 'pointer',
            padding: '0.5rem 0.75rem',
            borderRadius: '4px',
            textDecoration: 'underline',
          }}
        >
          {skipping ? 'Saltando...' : 'Explorar panel por mi cuenta'}
        </button>
      </header>

      {/* Contenedor central del Wizard */}
      <main style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2.5rem 1.5rem',
      }}>
        <div style={{
          width: '100%',
          maxWidth: step === 1 ? '680px' : '960px',
          backgroundColor: '#ffffff',
          border: '1px solid var(--panel-border, #e5e2dd)',
          borderRadius: '8px',
          boxShadow: 'var(--shadow-card)',
          padding: '2.5rem',
          transition: 'max-width 0.2s ease',
        }}>
          {/* PASO 1: Inmueble */}
          {step === 1 && (
            <form onSubmit={handleNextStep1} style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
              <div>
                <span style={{
                  fontSize: '0.72rem',
                  fontFamily: 'var(--font-mono)',
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  color: 'var(--brand-burgundy, #6b0008)',
                  display: 'block',
                  marginBottom: '0.4rem',
                }}>
                  Paso 1 · Tu patrimonio
                </span>
                <h1 style={{
                  fontSize: '1.75rem',
                  fontFamily: 'var(--font-serif)',
                  fontWeight: 400,
                  margin: '0 0 0.5rem 0',
                  color: 'var(--text-primary)',
                  letterSpacing: '-0.02em',
                }}>
                  Comencemos por tu primer inmueble
                </h1>
                <p style={{
                  fontSize: '0.92rem',
                  color: 'var(--text-secondary)',
                  margin: 0,
                  lineHeight: 1.5,
                }}>
                  Asigna un nombre para identificarlo en tu catálogo y su ubicación básica.
                </p>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
                    Nombre o Alias de la propiedad *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Ej. Ático en Fuencarral, Piso en Gran Vía..."
                    value={propertyName}
                    onChange={(e) => setPropertyName(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.75rem 1rem',
                      border: '1px solid var(--panel-border)',
                      borderRadius: '6px',
                      fontSize: '0.95rem',
                      outline: 'none',
                    }}
                    autoFocus
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
                      Tipo de inmueble
                    </label>
                    <select
                      value={propertyType}
                      onChange={(e) => setPropertyType(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '0.75rem 1rem',
                        border: '1px solid var(--panel-border)',
                        borderRadius: '6px',
                        fontSize: '0.95rem',
                        backgroundColor: '#ffffff',
                      }}
                    >
                      <option value="apartment">Vivienda / Piso</option>
                      <option value="house">Casa / Chalet</option>
                      <option value="commercial">Local Comercial</option>
                      <option value="garage">Plaza de Garaje</option>
                      <option value="land">Terreno</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
                      Ciudad / Población
                    </label>
                    <input
                      type="text"
                      placeholder="Ej. Madrid, Barcelona, Valencia..."
                      value={city}
                      onChange={(e) => setCity(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '0.75rem 1rem',
                        border: '1px solid var(--panel-border)',
                        borderRadius: '6px',
                        fontSize: '0.95rem',
                        outline: 'none',
                      }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
                    Calle o Dirección (opcional)
                  </label>
                  <input
                    type="text"
                    placeholder="Ej. Calle Gran Vía 42, 3º B"
                    value={street}
                    onChange={(e) => setStreet(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.75rem 1rem',
                      border: '1px solid var(--panel-border)',
                      borderRadius: '6px',
                      fontSize: '0.95rem',
                      outline: 'none',
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.75rem 1.5rem',
                    fontSize: '0.92rem',
                    backgroundColor: 'var(--brand-burgundy, #6b0008)',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                  }}
                >
                  Continuar a Fiscalidad <ArrowRight size={16} />
                </button>
              </div>
            </form>
          )}

          {/* PASO 2: Traslado al Borrador Real de Hacienda (Modelo 100 AEAT) */}
          {step === 2 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div>
                <span style={{
                  fontSize: '0.72rem',
                  fontFamily: 'var(--font-mono)',
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  color: 'var(--brand-burgundy, #6b0008)',
                  display: 'block',
                  marginBottom: '0.4rem',
                }}>
                  Paso 2 · Fiscalidad Oficial (Modelo 100 AEAT)
                </span>
                <h1 style={{
                  fontSize: '1.75rem',
                  fontFamily: 'var(--font-serif)',
                  fontWeight: 400,
                  margin: '0 0 0.5rem 0',
                  color: 'var(--text-primary)',
                  letterSpacing: '-0.02em',
                }}>
                  Tus ingresos y gastos, trasladados al borrador real de Hacienda
                </h1>
                <p style={{
                  fontSize: '0.92rem',
                  color: 'var(--text-secondary)',
                  margin: 0,
                  lineHeight: 1.5,
                }}>
                  Olvídate de calcular a mano o pagar a una gestoría: Arrendis clasifica automáticamente cada factura, cuota de comunidad, seguro y amortización legal en las casillas oficiales de la declaración de la Renta (Modelo 100).
                </p>
              </div>

              {/* Banner explícito de ejemplo ilustrativo */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.65rem',
                padding: '0.85rem 1rem',
                backgroundColor: 'var(--bg-tertiary, #f1f5f9)',
                border: '1px solid var(--panel-border, #e2e8f0)',
                borderRadius: '6px',
                fontSize: '0.82rem',
                color: 'var(--text-secondary, #475569)',
                lineHeight: 1.45,
              }}>
                <Info size={16} color="var(--brand-burgundy, #6b0008)" style={{ flexShrink: 0, marginTop: '2px' }} />
                <span>
                  <strong>Ejemplo ilustrativo:</strong> El siguiente extracto muestra cómo se estructura el borrador oficial. Al completar los datos fiscales de tu propiedad y registrar gastos, Arrendis generará automáticamente tu borrador oficial en PDF con el desglose exacto casilla por casilla para que puedas trasladar los importes a Renta Web manualmente sin complicaciones ni cálculos.
                </span>
              </div>

              {/* Simulador / Mockup Nativo del Borrador Oficial AEAT */}
              <div style={{
                backgroundColor: '#ffffff',
                border: '1px solid var(--panel-border, #e2e8f0)',
                borderRadius: '8px',
                overflow: 'hidden',
                boxShadow: 'var(--shadow-card, 0 1px 3px rgba(0,0,0,0.05))',
              }}>
                {/* Cabecera del Documento Tributario */}
                <div style={{
                  backgroundColor: '#f8fafc',
                  borderBottom: '1px solid var(--panel-border, #e2e8f0)',
                  padding: '0.85rem 1.25rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '0.5rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <FileText size={16} color="var(--brand-burgundy, #6b0008)" />
                    <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '0.02em' }}>
                      MODELO 100 AEAT · Rendimientos del Capital Inmobiliario
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{
                      fontSize: '0.7rem',
                      fontFamily: 'var(--font-mono)',
                      padding: '0.15rem 0.5rem',
                      borderRadius: '4px',
                      backgroundColor: '#eff6ff',
                      color: '#1d4ed8',
                      fontWeight: 600,
                    }}>
                      Ejemplo demostrativo
                    </span>
                    <span style={{
                      fontSize: '0.7rem',
                      fontFamily: 'var(--font-mono)',
                      padding: '0.15rem 0.5rem',
                      borderRadius: '4px',
                      backgroundColor: '#f1f5f9',
                      color: '#475569',
                    }}>
                      Ejercicio 2026
                    </span>
                  </div>
                </div>

                {/* Filas con Casillas Oficiales de la AEAT */}
                <div style={{ padding: '1rem 1.25rem', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                  
                  {/* Casilla 0102: Rendimientos Íntegros */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.65rem 0.85rem',
                    backgroundColor: 'var(--bg-primary, #f8fafc)',
                    borderRadius: '6px',
                    border: '1px solid var(--panel-border, #e2e8f0)',
                  }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', fontWeight: 700, color: 'var(--brand-burgundy, #6b0008)' }}>
                          [Casilla 0102]
                        </span>
                        <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                          Rendimientos Íntegros Computados
                        </strong>
                      </div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        Total de mensualidades de alquiler cobradas según tus contratos
                      </span>
                    </div>
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.95rem',
                      fontWeight: 600,
                      color: 'var(--text-primary)',
                    }}>
                      + 15.000,00 €
                    </span>
                  </div>

                  {/* Casillas 0105-0115: Gastos Deducibles */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.65rem 0.85rem',
                    backgroundColor: 'var(--bg-primary, #f8fafc)',
                    borderRadius: '6px',
                    border: '1px solid var(--panel-border, #e2e8f0)',
                  }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', fontWeight: 700, color: 'var(--brand-burgundy, #6b0008)' }}>
                          [Casillas 0105-0115]
                        </span>
                        <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                          Gastos Deducibles Clasificados
                        </strong>
                      </div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        Tributos (IBI), comunidad, seguros de hogar e impago, reparaciones y suministros (luz/agua/gas)
                      </span>
                    </div>
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.95rem',
                      fontWeight: 600,
                      color: 'var(--danger, #b91c1c)',
                    }}>
                      - 6.445,46 €
                    </span>
                  </div>

                  {/* Casilla 0131: Amortización Legal Inmueble (3%) */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.65rem 0.85rem',
                    backgroundColor: 'rgba(107, 0, 8, 0.03)',
                    borderRadius: '6px',
                    border: '1px solid rgba(107, 0, 8, 0.15)',
                  }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', fontWeight: 700, color: 'var(--brand-burgundy, #6b0008)' }}>
                          [Casilla 0131]
                        </span>
                        <strong style={{ fontSize: '0.85rem', color: 'var(--brand-burgundy, #6b0008)' }}>
                          Amortización del Inmueble (Art. 23.1.b LIRPF)
                        </strong>
                      </div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        Deducción del 3% anual sobre el valor de construcción calculada automáticamente por Arrendis
                      </span>
                    </div>
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.95rem',
                      fontWeight: 700,
                      color: 'var(--brand-burgundy, #6b0008)',
                    }}>
                      {estimate ? `- ${estimate.annual_amortization} €` : '- 3.204,00 €'}
                    </span>
                  </div>

                  {/* Casilla 0150: Reducción 60% Vivienda Habitual */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.65rem 0.85rem',
                    backgroundColor: 'var(--bg-primary, #f8fafc)',
                    borderRadius: '6px',
                    border: '1px solid var(--panel-border, #e2e8f0)',
                  }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', fontWeight: 700, color: 'var(--brand-burgundy, #6b0008)' }}>
                          [Casilla 0150]
                        </span>
                        <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                          Reducción por Vivienda Habitual (-60%)
                        </strong>
                      </div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        Beneficio fiscal estatal aplicable al arrendamiento residencial de larga duración
                      </span>
                    </div>
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.95rem',
                      fontWeight: 600,
                      color: 'var(--success, #047857)',
                    }}>
                      - 60,00%
                    </span>
                  </div>

                  {/* Casilla 0154: Rendimiento Neto Reducido */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.85rem 1rem',
                    backgroundColor: '#ffffff',
                    borderRadius: '6px',
                    border: '2px solid var(--panel-border, #cbd5e1)',
                    marginTop: '0.25rem',
                  }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                          [Casilla 0154]
                        </span>
                        <strong style={{ fontSize: '0.92rem', color: 'var(--text-primary)' }}>
                          Rendimiento Neto Reducido Final (Base Imponible)
                        </strong>
                      </div>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        Importe exacto sobre el que tributarás en Renta Web tras computar todas tus deducciones
                      </span>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '1.2rem',
                        fontWeight: 700,
                        color: 'var(--text-primary)',
                      }}>
                        ~ 2.140,22 €
                      </span>
                      <span style={{ display: 'block', fontSize: '0.72rem', color: 'var(--success, #047857)', fontWeight: 600 }}>
                        Ahorro total estimado: ~ 3.850 €
                      </span>
                    </div>
                  </div>
                </div>

                {/* Pie del bloque borrador */}
                <div style={{
                  padding: '0.75rem 1.25rem',
                  backgroundColor: '#f8fafc',
                  borderTop: '1px solid var(--panel-border, #e2e8f0)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  fontSize: '0.75rem',
                  color: 'var(--text-secondary)',
                }}>
                  <span>Al completar tu inmueble, podrás <strong>descargar el PDF oficial</strong> con todas las casillas preparadas para trasladarlas a Renta Web.</span>
                </div>
              </div>

              {/* Sección opcional: Estimación de compra */}
              <div style={{
                backgroundColor: 'var(--bg-primary, #f9f7f5)',
                border: '1px solid var(--panel-border, #e5e2dd)',
                borderRadius: '8px',
                padding: '1.25rem',
              }}>
                <div style={{ marginBottom: '0.85rem' }}>
                  <h4 style={{ margin: '0 0 0.25rem 0', fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                    Estimar la amortización de este inmueble (Opcional)
                  </h4>
                  <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Introduce el precio y año aproximados de adquisición para que Arrendis proyecte la Casilla 0131 en tu cartera:
                  </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 500, marginBottom: '0.35rem', color: 'var(--text-primary)' }}>
                      Precio de adquisición aproximado (€)
                    </label>
                    <input
                      type="number"
                      min="1000"
                      step="1000"
                      placeholder="210000"
                      value={purchasePrice}
                      onChange={(e) => setPurchasePrice(e.target.value === '' ? '' : Number(e.target.value))}
                      style={{
                        width: '100%',
                        padding: '0.65rem 0.85rem',
                        border: '1px solid var(--panel-border)',
                        borderRadius: '6px',
                        fontSize: '0.9rem',
                        fontFamily: 'var(--font-mono)',
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 500, marginBottom: '0.35rem', color: 'var(--text-primary)' }}>
                      Año de adquisición
                    </label>
                    <input
                      type="number"
                      min="1950"
                      max={currentYear}
                      placeholder="2021"
                      value={acquisitionYear}
                      onChange={(e) => setAcquisitionYear(e.target.value === '' ? '' : Number(e.target.value))}
                      style={{
                        width: '100%',
                        padding: '0.65rem 0.85rem',
                        border: '1px solid var(--panel-border)',
                        borderRadius: '6px',
                        fontSize: '0.9rem',
                        fontFamily: 'var(--font-mono)',
                      }}
                    />
                  </div>
                </div>

                {loadingEstimate ? (
                  <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Calculando según tablas de la AEAT...
                  </div>
                ) : estimate ? (
                  <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Deducción anual proyectada para Casilla 0131: <strong style={{ color: 'var(--brand-burgundy)' }}>~ {estimate.annual_amortization} € / año</strong> (ahorro en IRPF ~ {estimate.estimated_tax_savings_typical} € / año).
                  </div>
                ) : null}
              </div>

              {/* Botones de navegación del Paso 2 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  style={{
                    background: 'none',
                    border: '1px solid var(--panel-border)',
                    padding: '0.75rem 1.25rem',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    color: 'var(--text-secondary)',
                  }}
                >
                  <ArrowLeft size={16} /> Atrás
                </button>

                <button
                  type="button"
                  onClick={handleNextStep2}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.75rem 1.5rem',
                    fontSize: '0.92rem',
                    backgroundColor: 'var(--brand-burgundy, #6b0008)',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                  }}
                >
                  Continuar a Suministros <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* PASO 3: Automatización de Suministros y Facturas */}
          {step === 3 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
              <div>
                <span style={{
                  fontSize: '0.72rem',
                  fontFamily: 'var(--font-mono)',
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  color: 'var(--brand-burgundy, #6b0008)',
                  display: 'block',
                  marginBottom: '0.4rem',
                }}>
                  Paso 3 · Automatización de Suministros
                </span>
                <h1 style={{
                  fontSize: '1.75rem',
                  fontFamily: 'var(--font-serif)',
                  fontWeight: 400,
                  margin: '0 0 0.5rem 0',
                  color: 'var(--text-primary)',
                  letterSpacing: '-0.02em',
                }}>
                  Facturas de luz, agua y gas en piloto automático
                </h1>
                <p style={{
                  fontSize: '0.92rem',
                  color: 'var(--text-secondary)',
                  margin: 0,
                  lineHeight: 1.5,
                }}>
                  Los suministros que pagues como propietario son gastos 100% deducibles en tu Renta (Casilla 0113). Arrendis los ingesta, extrae y clasifica sin que tengas que introducir números a mano.
                </p>
              </div>

              {/* Los 2 Pilares Visuales de Automatización */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                gap: '1.25rem',
              }}>
                {/* Pilar 1: Buzón Inbound por Email */}
                <div style={{
                  backgroundColor: 'var(--bg-primary, #f9f7f5)',
                  border: '1px solid var(--panel-border, #e5e2dd)',
                  borderRadius: '8px',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.65rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Mail size={18} color="var(--brand-burgundy, #6b0008)" />
                      <strong style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                        1. Reenvío Automático por Email
                      </strong>
                    </div>
                    <span style={{
                      fontSize: '0.68rem',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 600,
                      padding: '0.15rem 0.45rem',
                      borderRadius: '4px',
                      backgroundColor: 'rgba(107, 0, 8, 0.08)',
                      color: 'var(--brand-burgundy, #6b0008)',
                    }}>
                      Cero trabajo manual
                    </span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                    Dispones de una dirección de correo exclusiva en Arrendis. Puedes darla directamente a Endesa o Iberdrola, o configurar una regla de reenvío automático en tu correo personal.
                  </p>

                  {/* Destacado del tutorial paso a paso */}
                  <div style={{
                    marginTop: 'auto',
                    padding: '0.7rem 0.85rem',
                    backgroundColor: '#ffffff',
                    borderRadius: '6px',
                    border: '1px solid var(--panel-border, #e5e2dd)',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '0.5rem',
                    fontSize: '0.78rem',
                    color: 'var(--text-primary)',
                    lineHeight: 1.4,
                  }}>
                    <BookOpen size={16} color="var(--brand-burgundy, #6b0008)" style={{ flexShrink: 0, marginTop: '2px' }} />
                    <span>
                      <strong>Tutorial paso a paso incluido:</strong> En tu panel dispones de una guía interactiva muy sencilla (con capturas) para crear la regla en Gmail u Outlook en solo 2 minutos.
                    </span>
                  </div>
                </div>

                {/* Pilar 2: Drag & Drop de PDFs */}
                <div style={{
                  backgroundColor: 'var(--bg-primary, #f9f7f5)',
                  border: '1px solid var(--panel-border, #e5e2dd)',
                  borderRadius: '8px',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.65rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <UploadCloud size={18} color="var(--success, #2b5329)" />
                      <strong style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                        2. Carga directa de PDFs
                      </strong>
                    </div>
                    <span style={{
                      fontSize: '0.68rem',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 600,
                      padding: '0.15rem 0.45rem',
                      borderRadius: '4px',
                      backgroundColor: 'rgba(43, 83, 41, 0.08)',
                      color: 'var(--success, #2b5329)',
                    }}>
                      Lectura en 2 segundos
                    </span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                    ¿Tienes facturas guardadas en tu ordenador? Arrástralas por lotes a tu panel. Nuestro motor OCR + IA lee el periodo, los importes, el IVA y las imputa a la casilla de suministros.
                  </p>

                  <div style={{
                    marginTop: 'auto',
                    padding: '0.7rem 0.85rem',
                    backgroundColor: '#ffffff',
                    borderRadius: '6px',
                    border: '1px solid var(--panel-border, #e5e2dd)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    fontSize: '0.78rem',
                    color: 'var(--text-secondary)',
                  }}>
                    <Check size={16} color="var(--success, #2b5329)" style={{ flexShrink: 0 }} />
                    <span>Compatible con Repsol, Iberdrola, Endesa, Naturgy, TotalEnergies y facturas municipales de agua.</span>
                  </div>
                </div>
              </div>

              {/* Explicación Pedagógica del CUPS */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.75rem',
                padding: '0.85rem 1rem',
                backgroundColor: '#ffffff',
                border: '1px solid var(--panel-border)',
                borderRadius: '6px',
              }}>
                <Zap size={18} color="var(--brand-burgundy, #6b0008)" style={{ flexShrink: 0, marginTop: '2px' }} />
                <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                  <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: '0.15rem' }}>
                    ¿Por qué utilizamos el código CUPS?
                  </strong>
                  El CUPS es el «DNI» de 20-22 caracteres de tu contador eléctrico. Arrendis lo lee automáticamente en tus facturas para saber a qué inmueble corresponde y contabilizar el gasto sin que tengas que hacer nada.
                </div>
              </div>

              {/* Formulario de Inputs: Renta y CUPS */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
                    Renta mensual percibida o estimada (€ / mes)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="10"
                    placeholder="950"
                    value={monthlyRent}
                    onChange={(e) => setMonthlyRent(e.target.value === '' ? '' : Number(e.target.value))}
                    style={{
                      width: '100%',
                      padding: '0.75rem 1rem',
                      border: '1px solid var(--panel-border)',
                      borderRadius: '6px',
                      fontSize: '0.95rem',
                      fontFamily: 'var(--font-mono)',
                    }}
                  />
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.3rem', display: 'block' }}>
                    Si el inmueble está alquilado, crearemos tu contrato inicial para computar los ingresos en la Casilla 0102.
                  </span>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                    <label style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                      Código CUPS de Electricidad (Opcional)
                    </label>
                    {!skipCupsNotice && (
                      <button
                        type="button"
                        onClick={() => {
                          setCupsElectricity('');
                          setSkipCupsNotice(true);
                        }}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--brand-burgundy, #6b0008)',
                          fontSize: '0.78rem',
                          cursor: 'pointer',
                          textDecoration: 'underline',
                          padding: 0,
                        }}
                      >
                        No tengo el CUPS a mano ahora
                      </button>
                    )}
                  </div>

                  {!skipCupsNotice ? (
                    <>
                      <input
                        type="text"
                        placeholder="ES0031..."
                        value={cupsElectricity}
                        onChange={(e) => setCupsElectricity(e.target.value)}
                        style={{
                          width: '100%',
                          padding: '0.75rem 1rem',
                          border: '1px solid var(--panel-border)',
                          borderRadius: '6px',
                          fontSize: '0.95rem',
                          fontFamily: 'var(--font-mono)',
                          letterSpacing: '0.04em',
                        }}
                      />
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.3rem', display: 'block' }}>
                        Puedes añadirlo ahora o dejar que Arrendis lo detecte automáticamente al subir tu primera factura.
                      </span>
                    </>
                  ) : (
                    <div style={{
                      padding: '0.75rem 1rem',
                      backgroundColor: 'var(--bg-primary, #f9f7f5)',
                      border: '1px solid var(--panel-border)',
                      borderRadius: '6px',
                      fontSize: '0.82rem',
                      color: 'var(--text-secondary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Check size={16} color="var(--success, #2b5329)" />
                        <span>Sin problema. Arrendis detectará el CUPS al subir tu primera factura PDF o podrás configurarlo en los ajustes.</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setSkipCupsNotice(false)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--brand-burgundy)',
                          fontSize: '0.75rem',
                          cursor: 'pointer',
                          textDecoration: 'underline',
                          marginLeft: '1rem',
                        }}
                      >
                        Introducir
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Botones de navegación del Paso 3 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  disabled={submitting}
                  style={{
                    background: 'none',
                    border: '1px solid var(--panel-border)',
                    padding: '0.75rem 1.25rem',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    color: 'var(--text-secondary)',
                  }}
                >
                  <ArrowLeft size={16} /> Atrás
                </button>

                <button
                  type="button"
                  onClick={handleFinish}
                  disabled={submitting}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.85rem 1.75rem',
                    fontSize: '0.95rem',
                    fontWeight: 500,
                    backgroundColor: 'var(--brand-burgundy, #6b0008)',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: submitting ? 'not-allowed' : 'pointer',
                    boxShadow: '0 2px 8px rgba(107, 0, 8, 0.2)',
                  }}
                >
                  {submitting ? 'Creando patrimonio...' : (
                    <>
                      <Check size={18} /> Finalizar y ver mi Patrimonio
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
