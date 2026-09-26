import { useState, useEffect } from "react";
import {
  TrendingUp,
  Sparkles,
  ExternalLink,
  Clock,
  RefreshCw,
  Building,
  Info,
  AlertCircle,
  HelpCircle,
} from "lucide-react";
import type { Property, PropertyValuation } from "../types";
import { getLatestValuation, requestValuation } from "../services/api";
import PhysicalAttributesModal from "./PhysicalAttributesModal";
import { ConfirmDialog } from "./ConfirmDialog";
import { useToast } from "./Toast";

interface MarketValuationPanelProps {
  property: Property;
  onPropertyUpdated: (updated: Property) => void;
}

export function formatFactorPercent(impact: number): string {
  const val = Math.abs(impact) <= 1.0 ? impact * 100 : impact;
  const sign = val > 0 ? "+" : "";
  return `${sign}${val.toFixed(1)}%`;
}

export default function MarketValuationPanel({
  property,
  onPropertyUpdated,
}: MarketValuationPanelProps) {
  const toast = useToast();
  const [valuation, setValuation] = useState<PropertyValuation | null>(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPhysicalModalOpen, setIsPhysicalModalOpen] = useState(false);
  const [isConfirmForceOpen, setIsConfirmForceOpen] = useState(false);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("es-ES", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const calculateGrossYield = (rentMedian: number, saleMedian: number): string => {
    if (!saleMedian || saleMedian <= 0) return "0.0";
    return ((rentMedian * 12 / saleMedian) * 100).toFixed(2);
  };

  const loadValuation = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getLatestValuation(property.id);
      setValuation(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al cargar la valoración de mercado";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadValuation();
  }, [property.id]);

  const handleRequestValuation = async (force = false) => {
    if (!property.surface_m2 || property.surface_m2 <= 0) {
      setIsPhysicalModalOpen(true);
      return;
    }

    setCalculating(true);
    setError(null);
    try {
      const freshValuation = await requestValuation(property.id, force);
      setValuation(freshValuation);
      if (freshValuation.is_cached) {
        toast.info("Valoración en periodo de enfriamiento: mostrando datos actualizados previamente.");
      } else {
        toast.success("Estimación de mercado completada con éxito.");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Fallo en la estimación de mercado";
      setError(msg);
      toast.error(msg);
    } finally {
      setCalculating(false);
    }
  };

  const hasMissingPhysicals = !property.surface_m2 || property.surface_m2 <= 0;

  const getConfidenceBadge = (confidence: string) => {
    switch (confidence.toLowerCase()) {
      case "high":
        return { label: "Confianza Alta", className: "badge-confidence-high" };
      case "medium":
        return { label: "Confianza Media", className: "badge-confidence-medium" };
      default:
        return { label: "Confianza Básica", className: "badge-confidence-low" };
    }
  };

  return (
    <div className="market-valuation-panel">
      {/* Banner de Atributos Físicos Faltantes */}
      {hasMissingPhysicals && (
        <div className="valuation-alert-banner warning">
          <div className="alert-content">
            <AlertCircle size={20} className="alert-icon" />
            <div>
              <h4 style={{ margin: "0 0 4px", fontSize: "0.95rem", fontWeight: 600 }}>
                Se requiere especificar la superficie construida
              </h4>
              <p style={{ margin: 0, fontSize: "0.85rem", opacity: 0.9 }}>
                Para estimar el precio de venta y alquiler comparando con ofertas reales de la zona, debes indicar los metros cuadrados de la vivienda.
              </p>
            </div>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setIsPhysicalModalOpen(true)}
          >
            Completar características
          </button>
        </div>
      )}

      {/* Header Editorial del Panel */}
      <div className="valuation-header-card">
        <div className="header-info">
          <div className="title-row" style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
            <h3 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 700, letterSpacing: "-0.01em" }}>
              Estimación de Mercado y Orientación de Renta
            </h3>
            {valuation && (
              <span className={`confidence-pill ${getConfidenceBadge(valuation.confidence).className}`}>
                {getConfidenceBadge(valuation.confidence).label}
              </span>
            )}
          </div>
          <p style={{ margin: "6px 0 0", color: "var(--text-secondary, #64748b)", fontSize: "0.875rem" }}>
            Análisis algorítmico asistido por IA y contrastado con testigos reales en Google Search para{" "}
            <strong>{property.name}</strong> ({property.address.city}, CP {property.address.postal_code}).
          </p>
        </div>

        <div className="header-actions">
          {valuation && valuation.cooldown_days_remaining !== undefined && valuation.cooldown_days_remaining > 0 ? (
            <div className="cooldown-action-group" style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
              <span className="cooldown-pill" title="Límite temporal para optimizar consultas de mercado">
                <Clock size={13} style={{ marginRight: "4px" }} />
                Próxima revisión en {valuation.cooldown_days_remaining} {valuation.cooldown_days_remaining === 1 ? "día" : "días"}
              </span>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setIsConfirmForceOpen(true)}
                disabled={calculating || hasMissingPhysicals}
                title="Forzar un recálculo si has realizado reformas o modificaciones físicas"
              >
                <RefreshCw size={13} className={calculating ? "spin" : ""} style={{ marginRight: "4px" }} />
                Forzar recálculo
              </button>
            </div>
          ) : (
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => handleRequestValuation(false)}
              disabled={calculating || hasMissingPhysicals}
            >
              <Sparkles size={16} className={calculating ? "spin" : ""} style={{ marginRight: "6px" }} />
              {valuation ? "Actualizar estimación" : "Solicitar estimación de mercado"}
            </button>
          )}

          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => setIsPhysicalModalOpen(true)}
            title="Editar características físicas del inmueble"
          >
            <Building size={14} style={{ marginRight: "4px" }} />
            {property.surface_m2 ? `${property.surface_m2} m²` : "Editar datos físicos"}
          </button>
        </div>
      </div>

      {/* Estado Calculando en Progreso */}
      {calculating && (
        <div className="valuation-calculating-box">
          <div className="pulse-indicator">
            <Sparkles size={28} className="spin text-primary" />
          </div>
          <h4 style={{ margin: "12px 0 4px", fontSize: "1.05rem" }}>
            Rastreando testigos y comparables de mercado...
          </h4>
          <p style={{ margin: 0, fontSize: "0.875rem", color: "var(--text-secondary, #64748b)" }}>
            Consultando en vivo portales inmobiliarios de la zona y sintetizando horquillas de precios ponderadas. Esto suele tomar entre 10 y 15 segundos.
          </p>
        </div>
      )}

      {/* Error Banner */}
      {error && !calculating && (
        <div className="valuation-alert-banner error" style={{ marginTop: "16px" }}>
          <AlertCircle size={18} className="alert-icon" />
          <div style={{ fontSize: "0.875rem" }}>{error}</div>
        </div>
      )}

      {/* Estado Inicial Vacío */}
      {!loading && !calculating && !valuation && (
        <div className="valuation-empty-hero">
          <div className="empty-icon-wrap">
            <TrendingUp size={36} />
          </div>
          <h3 style={{ margin: "16px 0 8px", fontSize: "1.15rem", fontWeight: 600 }}>
            Sin estimación de mercado registrada todavía
          </h3>
          <p style={{ margin: "0 auto 20px", maxWidth: "540px", fontSize: "0.9rem", color: "var(--text-secondary, #64748b)", lineHeight: 1.5 }}>
            Obtén en segundos una horquilla orientativa de venta y de renta mensual para tu propiedad basada en datos actualizados y testigos reales comparables de tu zona.
          </p>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => handleRequestValuation(false)}
            disabled={hasMissingPhysicals}
          >
            <Sparkles size={16} style={{ marginRight: "6px" }} />
            Calcular primera estimación
          </button>
        </div>
      )}

      {/* Resultados de Valoración */}
      {!calculating && valuation && (
        <div className="valuation-results-container" style={{ marginTop: "20px" }}>
          {/* Hero Cards: Venta y Alquiler */}
          <div className="valuation-hero-grid">
            {/* Tarjeta Venta */}
            <div className="valuation-card hero sale">
              <div className="card-top-tag">Valor de Compraventa Estimado</div>
              <div className="main-price-figure">
                {formatCurrency(valuation.sale_range.median)}
              </div>
              <div className="range-interval">
                <span>Mín. {formatCurrency(valuation.sale_range.min)}</span>
                <span className="dot">•</span>
                <span>Máx. {formatCurrency(valuation.sale_range.max)}</span>
              </div>
              <div className="card-footer-note">
                {property.surface_m2
                  ? `~${Math.round(valuation.sale_range.median / property.surface_m2)} €/m² de valor medio en zona`
                  : "Precio de referencia calculado para el activo"}
              </div>
            </div>

            {/* Tarjeta Alquiler */}
            <div className="valuation-card hero rent">
              <div className="card-top-tag">Renta Mensual Orientativa</div>
              <div className="main-price-figure">
                {formatCurrency(valuation.rent_range.median)}
                <span className="per-month">/mes</span>
              </div>
              <div className="range-interval">
                <span>Mín. {formatCurrency(valuation.rent_range.min)}/m</span>
                <span className="dot">•</span>
                <span>Máx. {formatCurrency(valuation.rent_range.max)}/m</span>
              </div>
              <div className="card-footer-note">
                {property.surface_m2
                  ? `~${(valuation.rent_range.median / property.surface_m2).toFixed(1)} €/m²/mes estimado`
                  : "Renta de mercado recomendada"}
              </div>
            </div>

            {/* Tarjeta Yield Estimado */}
            <div className="valuation-card hero yield">
              <div className="card-top-tag">Rentabilidad Bruta Teórica</div>
              <div className="main-price-figure" style={{ color: "var(--color-primary, #0284c7)" }}>
                {calculateGrossYield(valuation.rent_range.median, valuation.sale_range.median)}%
              </div>
              <div className="range-interval">
                <span>Renta anual: {formatCurrency(valuation.rent_range.median * 12)}</span>
              </div>
              <div className="card-footer-note">
                Yield bruto calculado sobre valor mediano estimado
              </div>
            </div>
          </div>

          {/* Desglose de Factores Explicativos */}
          {valuation.reasoning_factors && valuation.reasoning_factors.length > 0 && (
            <div className="valuation-section" style={{ marginTop: "24px" }}>
              <div className="section-title-wrap">
                <h4 style={{ margin: "0 0 4px", fontSize: "1rem", fontWeight: 600 }}>
                  Factores de Ponderación y Ajuste de Valor
                </h4>
                <p style={{ margin: 0, fontSize: "0.825rem", color: "var(--text-secondary, #64748b)" }}>
                  Elementos clave que modulan la estimación al alza o a la baja respecto a la media de la zona.
                </p>
              </div>

              <div className="factors-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "12px", marginTop: "12px" }}>
                {valuation.reasoning_factors.map((factor, idx) => {
                  const isPositive = factor.impact_percent >= 0;
                  return (
                    <div key={idx} className="factor-item-card">
                      <div className="factor-top" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                        <span className="factor-name" style={{ fontWeight: 600, fontSize: "0.875rem" }}>
                          {factor.factor_name}
                        </span>
                        <span className={`factor-impact-pill ${isPositive ? "positive" : "negative"}`}>
                          {formatFactorPercent(factor.impact_percent)}
                        </span>
                      </div>
                      <p className="factor-desc" style={{ margin: 0, fontSize: "0.8rem", color: "var(--text-secondary, #64748b)", lineHeight: 1.4 }}>
                        {factor.description}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Notas Cualitativas de Mercado */}
          {valuation.raw_notes && (
            <div className="valuation-section" style={{ marginTop: "24px" }}>
              <div className="valuation-notes-card">
                <Info size={16} className="notes-icon" style={{ marginTop: "2px", flexShrink: 0 }} />
                <div style={{ fontSize: "0.85rem", lineHeight: 1.5, color: "var(--text-primary, #334155)" }}>
                  <strong>Análisis del entorno:</strong> {valuation.raw_notes}
                </div>
              </div>
            </div>
          )}

          {/* Testigos y Enlaces Web Reales (Grounding Sources) */}
          {valuation.sources && valuation.sources.length > 0 && (
            <div className="valuation-section" style={{ marginTop: "24px" }}>
              <div className="section-title-wrap">
                <h4 style={{ margin: "0 0 4px", fontSize: "1rem", fontWeight: 600 }}>
                  Testigos Comparables Localizados en Búsqueda Web
                </h4>
                <p style={{ margin: 0, fontSize: "0.825rem", color: "var(--text-secondary, #64748b)" }}>
                  Anuncios reales indexados y consultados por la IA para anclar las horquillas de precios a la oferta actual.
                </p>
              </div>

              <div className="sources-list" style={{ marginTop: "12px", display: "flex", flexDirection: "column", gap: "8px" }}>
                {valuation.sources.map((src, idx) => {
                  const isSafeUrl = src.url.startsWith("http://") || src.url.startsWith("https://");
                  return (
                    <div key={idx} className="source-row-card">
                      <div className="source-info">
                        {isSafeUrl ? (
                          <a
                            href={src.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="source-title-link"
                          >
                            <span>{src.title || "Anuncio comparable"}</span>
                            <ExternalLink size={13} style={{ marginLeft: "4px", flexShrink: 0 }} />
                          </a>
                        ) : (
                          <span style={{ fontWeight: 500, fontSize: "0.875rem" }}>{src.title}</span>
                        )}
                        <span className="source-domain">
                          {src.url.replace(/^https?:\/\/(www\.)?/, "").split("/")[0]}
                        </span>
                      </div>

                      <div className="source-specs">
                        {src.surface_m2 && <span className="spec-badge">{src.surface_m2} m²</span>}
                        {src.price && <span className="spec-price">{formatCurrency(src.price)}</span>}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Descargo Legal y Metodológico */}
          <div className="valuation-disclaimer-box" style={{ marginTop: "28px" }}>
            <HelpCircle size={15} style={{ flexShrink: 0, marginTop: "2px" }} />
            <p style={{ margin: 0, fontSize: "0.775rem", color: "var(--text-secondary, #64748b)", lineHeight: 1.45 }}>
              <strong>Aviso legal:</strong> Esta estimación es puramente informativa y orientativa, generada mediante modelos de lenguaje con búsqueda en tiempo real sobre portales inmobiliarios públicos. No constituye una tasación oficial homologada (norma ECO hipotecaria) ni un certificado pericial con validez jurídica o bancaria.
            </p>
          </div>
        </div>
      )}

      {/* Modal para Editar Atributos Físicos */}
      <PhysicalAttributesModal
        isOpen={isPhysicalModalOpen}
        onClose={() => setIsPhysicalModalOpen(false)}
        property={property}
        onSuccess={(updated) => {
          onPropertyUpdated(updated);
          toast.success("Características físicas actualizadas correctamente.");
        }}
      />

      {/* Diálogo de Confirmación para Recálculo Forzado */}
      <ConfirmDialog
        isOpen={isConfirmForceOpen}
        title="¿Forzar nueva estimación de mercado?"
        message="Aún quedan días en el periodo de enfriamiento estándar de tu propiedad. Si realizas una nueva estimación ahora, se consultarán testigos en tiempo real consumiendo cuota de búsqueda. ¿Deseas continuar?"
        confirmLabel="Sí, actualizar ahora"
        variant="warning"
        onConfirm={() => {
          setIsConfirmForceOpen(false);
          handleRequestValuation(true);
        }}
        onCancel={() => setIsConfirmForceOpen(false)}
      />
    </div>
  );
}
