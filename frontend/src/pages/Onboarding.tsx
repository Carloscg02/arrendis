import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Building, 
  ArrowRight, 
  ArrowLeft, 
  Check, 
  ShieldCheck, 
  FileText, 
  Mail, 
  UploadCloud, 
  Eye, 
  X, 
  Zap,
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
  const [isPdfModalOpen, setIsPdfModalOpen] = useState(false);

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
      // Enviar con query param ?welcome=true para activar el banner de bienvenida guiado
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

          {/* PASO 2: Fiscalidad Oficial · Modelo 100 AEAT */}
          {step === 2 && (
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
                  Tu borrador tributario generado al vuelo
                </h1>
                <p style={{
                  fontSize: '0.92rem',
                  color: 'var(--text-secondary)',
                  margin: 0,
                  lineHeight: 1.5,
                }}>
                  Hacienda permite deducir el <strong>3% anual</strong> del valor de construcción de tus inmuebles arrendados (Art. 23.1.b LIRPF). Arrendis traslada esta amortización y todos tus gastos directamente a las casillas oficiales de la Renta.
                </p>
              </div>

              {/* Grid de 2 Columnas: Izquierda Inputs/Cálculo - Derecha Visualizador Documental */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
                gap: '1.75rem',
                alignItems: 'start',
              }}>
                {/* Columna Izquierda: Parámetros y Simulación */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
                        Precio de compra aprox. (€)
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
                          padding: '0.75rem 1rem',
                          border: '1px solid var(--panel-border)',
                          borderRadius: '6px',
                          fontSize: '0.95rem',
                          fontFamily: 'var(--font-mono)',
                        }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
                        Año de compra
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
                          padding: '0.75rem 1rem',
                          border: '1px solid var(--panel-border)',
                          borderRadius: '6px',
                          fontSize: '0.95rem',
                          fontFamily: 'var(--font-mono)',
                        }}
                      />
                    </div>
                  </div>

                  {/* Tarjeta de cálculo en vivo */}
                  <div style={{
                    backgroundColor: 'var(--bg-primary, #f9f7f5)',
                    border: '1px solid var(--panel-border, #e5e2dd)',
                    borderRadius: '8px',
                    padding: '1.25rem',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <Building size={16} color="var(--brand-burgundy, #6b0008)" />
                        <span style={{
                          fontSize: '0.75rem',
                          fontFamily: 'var(--font-mono)',
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          letterSpacing: '0.05em',
                          color: 'var(--brand-burgundy, #6b0008)',
                        }}>
                          Deducción Anual (Art. 23.1.b)
                        </span>
                      </div>
                      <span style={{
                        fontSize: '0.7rem',
                        fontFamily: 'var(--font-mono)',
                        padding: '0.15rem 0.45rem',
                        borderRadius: '4px',
                        backgroundColor: 'rgba(107, 0, 8, 0.08)',
                        color: 'var(--brand-burgundy, #6b0008)',
                        fontWeight: 600,
                      }}>
                        Casilla 0131 AEAT
                      </span>
                    </div>

                    {loadingEstimate ? (
                      <div style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                        Calculando según tablas de la AEAT...
                      </div>
                    ) : estimate ? (
                      <div>
                        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.2rem' }}>
                          <span style={{
                            fontSize: '2rem',
                            fontFamily: 'var(--font-serif)',
                            fontWeight: 500,
                            color: 'var(--text-primary)',
                          }}>
                            ~ {estimate.annual_amortization} €
                          </span>
                          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>/ año deducibles</span>
                        </div>

                        <p style={{
                          fontSize: '0.85rem',
                          color: 'var(--text-secondary)',
                          margin: '0 0 0.85rem 0',
                          lineHeight: 1.4,
                        }}>
                          Ahorro estimado en IRPF: <strong style={{ color: 'var(--success, #2b5329)' }}>~ {estimate.estimated_tax_savings_typical} € / año</strong> (tipo marginal medio ~30%).
                        </p>

                        {/* Desglose de parámetros legales */}
                        <div style={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '0.35rem',
                          padding: '0.75rem',
                          backgroundColor: '#ffffff',
                          borderRadius: '6px',
                          border: '1px solid var(--panel-border-subtle, #eeeae4)',
                          fontSize: '0.78rem',
                          color: 'var(--text-secondary)',
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span>Valor estimado de construcción (70%):</span>
                            <strong style={{ fontFamily: 'var(--font-mono)' }}>~ {estimate.estimated_construction_value} €</strong>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span>Suelo no amortizable (30%):</span>
                            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>~ {estimate.estimated_land_value} €</span>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid #f1eee9', paddingTop: '0.35rem', marginTop: '0.2rem' }}>
                            <span>Tipo de amortización anual:</span>
                            <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--brand-burgundy)' }}>3,00%</strong>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                        Introduce un precio de compra para ver el cálculo.
                      </div>
                    )}
                  </div>

                  <div style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '0.5rem',
                    fontSize: '0.78rem',
                    color: 'var(--text-muted)',
                    lineHeight: 1.4,
                  }}>
                    <ShieldCheck size={16} color="var(--brand-burgundy)" style={{ flexShrink: 0, marginTop: '2px' }} />
                    <span>
                      Sin hojas de cálculo ni errores manuales. Arrendis calcula la depreciación acumulada y genera tu liquidación oficial al final del año.
                    </span>
                  </div>
                </div>

                {/* Columna Derecha: El Borrador Oficial Modelo 100 */}
                <div style={{
                  backgroundColor: '#ffffff',
                  border: '1px solid var(--panel-border, #e5e2dd)',
                  borderRadius: '8px',
                  padding: '1.25rem',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.85rem',
                }}>
                  {/* Encabezado del documento */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--panel-border)', paddingBottom: '0.65rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <FileText size={16} color="var(--brand-burgundy, #6b0008)" />
                      <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        Borrador Oficial Modelo 100
                      </span>
                    </div>
                    <span style={{
                      fontSize: '0.7rem',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 600,
                      padding: '0.15rem 0.45rem',
                      borderRadius: '4px',
                      backgroundColor: '#eff6ff',
                      color: '#1d4ed8',
                    }}>
                      AEAT · PDF Oficial
                    </span>
                  </div>

                  {/* Previsualización del documento con alta definición */}
                  <div 
                    onClick={() => setIsPdfModalOpen(true)}
                    style={{
                      position: 'relative',
                      borderRadius: '6px',
                      overflow: 'hidden',
                      border: '1px solid var(--panel-border)',
                      cursor: 'pointer',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                      maxHeight: '220px',
                      backgroundColor: '#f8fafc',
                    }}
                    title="Haz clic para ver el borrador a tamaño completo"
                  >
                    <img 
                      src="/onboarding/borrador-modelo-100.png" 
                      alt="Borrador Fiscal Oficial Modelo 100 AEAT"
                      style={{
                        width: '100%',
                        height: 'auto',
                        display: 'block',
                        objectFit: 'cover',
                        objectPosition: 'top',
                      }}
                      onError={(e) => {
                        // Fallback si la imagen aún no está cargada
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                    {/* Overlay botón para zoom */}
                    <div style={{
                      position: 'absolute',
                      inset: 0,
                      backgroundColor: 'rgba(15, 23, 42, 0.4)',
                      opacity: 0,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '0.4rem',
                      color: '#ffffff',
                      fontSize: '0.85rem',
                      fontWeight: 500,
                      transition: 'opacity 0.2s ease',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                    onMouseLeave={(e) => e.currentTarget.style.opacity = '0'}
                    >
                      <Eye size={18} /> Ver borrador completo
                    </div>
                  </div>

                  {/* Lista de Casillas Oficiales Deducibles que gestiona Arrendis */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.2rem 0' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>[0102] Rendimientos Íntegros</span>
                      <span>Alquileres computados</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.2rem 0' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>[0105-0117] Gastos Deducibles</span>
                      <span>IBI, seguros, comunidad, suministros</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.2rem 0' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--brand-burgundy)' }}>[0131] Amortización Inmueble</span>
                      <strong style={{ color: 'var(--brand-burgundy)' }}>3% s/construcción</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.2rem 0' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>[0154] Rendimiento Neto</span>
                      <span>Listo para trasladar a Renta Web</span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => setIsPdfModalOpen(true)}
                    className="btn btn-secondary btn-sm"
                    style={{
                      width: '100%',
                      fontSize: '0.8rem',
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '0.4rem',
                      padding: '0.5rem',
                    }}
                  >
                    <Eye size={14} /> Ampliar Borrador Oficial (PDF)
                  </button>
                </div>
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
                  Olvídate de contabilizar facturas a mano
                </h1>
                <p style={{
                  fontSize: '0.92rem',
                  color: 'var(--text-secondary)',
                  margin: 0,
                  lineHeight: 1.5,
                }}>
                  Las facturas de luz, gas y agua que pagues tú son <strong>gastos 100% deducibles en tu Renta</strong> (Casilla 0113). Arrendis las ingesta, extrae y clasifica automáticamente.
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
                  gap: '0.5rem',
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
                      Cero intervención
                    </span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                    Tendrás un buzón exclusivo de Arrendis. Configura una regla en tu correo o facilita esa dirección a Endesa, Iberdrola o Repsol: las facturas que lleguen se registrarán solas en segundo plano con IA.
                  </p>
                </div>

                {/* Pilar 2: Drag & Drop de PDFs */}
                <div style={{
                  backgroundColor: 'var(--bg-primary, #f9f7f5)',
                  border: '1px solid var(--panel-border, #e5e2dd)',
                  borderRadius: '8px',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
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
                    ¿Tienes facturas guardadas en tu ordenador? Arrástralas por lotes a tu panel. Nuestro motor OCR lee el periodo, los importes con desglose de IVA y las imputa a la casilla de suministros.
                  </p>
                </div>
              </div>

              {/* Explicación Pedagógica del CUPS */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.75rem',
                padding: '1rem',
                backgroundColor: '#ffffff',
                border: '1px solid var(--panel-border)',
                borderRadius: '6px',
              }}>
                <Zap size={18} color="var(--brand-burgundy, #6b0008)" style={{ flexShrink: 0, marginTop: '2px' }} />
                <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                  <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: '0.2rem' }}>
                    ¿Por qué utilizamos el código CUPS?
                  </strong>
                  El CUPS es el «DNI» de 20-22 caracteres de tu contador eléctrico (aparece arriba a la derecha en cualquier factura). Arrendis lee el CUPS de la factura para saber a qué piso corresponde y asignarla sin errores.
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

      {/* Modal Zoom Borrador Fiscal Oficial AEAT */}
      {isPdfModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.75)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2rem',
          }}
          onClick={() => setIsPdfModalOpen(false)}
        >
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '8px',
              maxWidth: '850px',
              maxHeight: '90vh',
              width: '100%',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Cabecera del modal */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '1rem 1.5rem',
              borderBottom: '1px solid var(--panel-border)',
              backgroundColor: '#f8fafc',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FileText size={18} color="var(--brand-burgundy, #6b0008)" />
                <strong style={{ fontSize: '1rem', color: 'var(--text-primary)' }}>
                  Borrador Fiscal Oficial — Rendimientos del Capital Inmobiliario (Modelo 100)
                </strong>
              </div>
              <button
                onClick={() => setIsPdfModalOpen(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--text-muted)',
                  padding: '0.25rem',
                  display: 'flex',
                }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Contenido scrolleable con la imagen en alta definición */}
            <div style={{
              overflowY: 'auto',
              padding: '1.5rem',
              display: 'flex',
              justifyContent: 'center',
              backgroundColor: '#f1f5f9',
            }}>
              <img
                src="/onboarding/borrador-modelo-100.png"
                alt="Borrador Oficial Completo"
                style={{
                  maxWidth: '100%',
                  height: 'auto',
                  borderRadius: '4px',
                  boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
                }}
              />
            </div>

            {/* Pie del modal */}
            <div style={{
              padding: '0.85rem 1.5rem',
              borderTop: '1px solid var(--panel-border)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backgroundColor: '#ffffff',
            }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Arrendis genera automáticamente este PDF descargable para cada ejercicio fiscal.
              </span>
              <button
                onClick={() => setIsPdfModalOpen(false)}
                className="btn btn-secondary btn-sm"
              >
                Cerrar vista previa
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
