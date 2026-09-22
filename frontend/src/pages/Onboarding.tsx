import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building, ArrowRight, ArrowLeft, Check, ShieldCheck } from 'lucide-react';
import ArrendisLogo from '../components/ArrendisLogo';
import { getQuickFiscalEstimate, bootstrapOnboarding, skipOnboarding } from '../services/api';
import type { QuickEstimateResponse } from '../types';
import { useToast } from '../components/Toast';

export default function Onboarding() {
  const navigate = useNavigate();
  const toast = useToast();

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
      navigate('/properties');
    } catch (err: any) {
      toast.error(err.message || 'Error al omitir la guía.');
      navigate('/properties');
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

      toast.success('¡Patrimonio registrado con éxito! Tu estimación fiscal está activa.');
      navigate(`/properties/${res.id}`);
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
          maxWidth: '680px',
          backgroundColor: '#ffffff',
          border: '1px solid var(--panel-border, #e5e2dd)',
          borderRadius: '8px',
          boxShadow: 'var(--shadow-card)',
          padding: '2.5rem',
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
                    placeholder="Ej. Ático en Fuencarral, Piso en Valencia..."
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

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
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
                      placeholder="Ej. Madrid, Barcelona..."
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
                    placeholder="Ej. Calle Mayor 14, 3º B"
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

          {/* PASO 2: La Ventaja Fiscal (Momento 'Aha!') */}
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
                  Paso 2 · El superpoder de Arrendis
                </span>
                <h1 style={{
                  fontSize: '1.75rem',
                  fontFamily: 'var(--font-serif)',
                  fontWeight: 400,
                  margin: '0 0 0.5rem 0',
                  color: 'var(--text-primary)',
                  letterSpacing: '-0.02em',
                }}>
                  Tu deducción legal en la Renta (IRPF)
                </h1>
                <p style={{
                  fontSize: '0.92rem',
                  color: 'var(--text-secondary)',
                  margin: 0,
                  lineHeight: 1.5,
                }}>
                  Hacienda te permite amortizar el <strong>3% anual</strong> del valor de construcción de tus inmuebles arrendados. Introduzcamos el coste aproximado para estimar tu ventaja fiscal:
                </p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
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

              {/* Tarjeta de cálculo en vivo (El 'Aha! moment') */}
              <div style={{
                backgroundColor: 'var(--bg-primary, #f9f7f5)',
                border: '1px solid var(--panel-border, #e5e2dd)',
                borderRadius: '8px',
                padding: '1.5rem',
                position: 'relative',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <Building size={18} color="var(--brand-burgundy, #6b0008)" />
                  <span style={{
                    fontSize: '0.78rem',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    color: 'var(--brand-burgundy, #6b0008)',
                  }}>
                    Amortización Inmueble (Art. 23.1.b LIRPF)
                  </span>
                </div>

                {loadingEstimate ? (
                  <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                    Calculando según tablas de la AEAT...
                  </div>
                ) : estimate ? (
                  <div>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.25rem' }}>
                      <span style={{
                        fontSize: '2.25rem',
                        fontFamily: 'var(--font-serif)',
                        fontWeight: 500,
                        color: 'var(--text-primary)',
                      }}>
                        ~ {estimate.annual_amortization} €
                      </span>
                      <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>/ año deducibles</span>
                    </div>

                    <p style={{
                      fontSize: '0.88rem',
                      color: 'var(--text-secondary)',
                      margin: '0 0 1rem 0',
                      lineHeight: 1.45,
                    }}>
                      Ahorro estimado en IRPF: <strong style={{ color: 'var(--success, #2b5329)' }}>~ {estimate.estimated_tax_savings_typical} € / año</strong> (tipo medio ~30%).
                    </p>

                    <div style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '0.5rem',
                      padding: '0.75rem',
                      backgroundColor: '#ffffff',
                      borderRadius: '6px',
                      border: '1px solid var(--panel-border-subtle, #eeeae4)',
                      fontSize: '0.8rem',
                      color: 'var(--text-muted)',
                      lineHeight: 1.4,
                    }}>
                      <ShieldCheck size={16} color="var(--brand-burgundy)" style={{ flexShrink: 0, marginTop: '2px' }} />
                      <span>
                        {estimate.disclaimer} Más adelante podrás afinar los decimales exactos con tu recibo del IBI.
                      </span>
                    </div>
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    Introduce un precio de compra para ver el cálculo.
                  </div>
                )}
              </div>

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

          {/* PASO 3: Alquiler y Automatización */}
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
                  Paso 3 · Renta & Automatización
                </span>
                <h1 style={{
                  fontSize: '1.75rem',
                  fontFamily: 'var(--font-serif)',
                  fontWeight: 400,
                  margin: '0 0 0.5rem 0',
                  color: 'var(--text-primary)',
                  letterSpacing: '-0.02em',
                }}>
                  Renta y lectura automática de facturas
                </h1>
                <p style={{
                  fontSize: '0.92rem',
                  color: 'var(--text-secondary)',
                  margin: 0,
                  lineHeight: 1.5,
                }}>
                  Los suministros (luz, gas, agua) que pagues tú son <strong>gastos deducibles al 100%</strong>. Arrendis puede registrarlos automáticamente desde tus facturas.
                </p>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
                    Renta mensual del alquiler (€ / mes)
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
                    Si el inmueble está alquilado, crearemos tu contrato inicial para computar los ingresos.
                  </span>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
                    Código CUPS de Electricidad (Opcional)
                  </label>
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
                    Encontrarás el CUPS en cualquier factura de Endesa, Iberdrola, Naturgy, etc. Puedes añadirlo ahora o más tarde.
                  </span>
                </div>
              </div>

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
