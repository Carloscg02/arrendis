import { useNavigate } from "react-router-dom";
import { MapPin, ArrowRight, Building, Zap, FileText, CheckCircle2 } from "lucide-react";
import type { Property } from "../types";
import { BACKEND_STATIC_URL } from "../services/api";

interface Props {
  property: Property;
}

export default function PropertyCard({ property }: Props) {
  const navigate = useNavigate();

  const getStatusClass = (status: string) => {
    switch (status.toLowerCase()) {
      case "available":
        return "badge-success";
      case "rented":
        return "badge-primary";
      case "maintenance":
        return "badge-warning";
      default:
        return "badge-neutral";
    }
  };

  const translateStatus = (status: string) => {
    switch (status.toLowerCase()) {
      case "available": return "Disponible";
      case "rented": return "Alquilado";
      case "maintenance": return "Mantenimiento";
      default: return status;
    }
  };

  const translateType = (type: string) => {
    switch (type.toLowerCase()) {
      case "apartment": return "Piso Residencial";
      case "house": return "Vivienda Unifamiliar";
      case "commercial": return "Local Comercial";
      case "garage": return "Plaza Garaje";
      case "land": return "Suelo / Finca";
      default: return type;
    }
  };

  // Supplies count
  const cupsCount = [property.cups_electricity, property.cups_gas, property.cups_water].filter(Boolean).length;

  const imageUrl = property.image_url ? `${BACKEND_STATIC_URL}${property.image_url}` : null;

  return (
    <article
      className="property-dossier-card"
      onClick={() => navigate(`/properties/${property.id}`)}
      tabIndex={0}
      role="button"
      onKeyDown={(e) => e.key === 'Enter' && navigate(`/properties/${property.id}`)}
    >
      <div
        className={`property-dossier-image ${!imageUrl ? 'property-dossier-image--placeholder' : ''}`}
        style={imageUrl ? { backgroundImage: `url(${imageUrl})` } : undefined}
      >
        {!imageUrl && (
          <div className="property-dossier-placeholder-content">
            <Building size={28} strokeWidth={1.25} />
            <span className="mono-caption">EXPEDIENTE S/FOTO</span>
          </div>
        )}
      </div>

      {/* 2. Columna Central: Identidad del Inmueble y Ubicación */}
      <div className="property-dossier-main">
        <div className="property-dossier-top">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <span className={`badge ${getStatusClass(property.status)}`}>
              {translateStatus(property.status)}
            </span>
            <span className="badge badge-outline">
              {translateType(property.property_type)}
            </span>
          </div>
        </div>

        <div className="property-dossier-title-area">
          <h2 className="property-dossier-name">{property.name}</h2>
          <p className="property-dossier-address">
            <MapPin size={13} style={{ flexShrink: 0 }} />
            <span>{property.address.street}, {property.address.city} {property.address.postal_code}</span>
          </p>
        </div>

        <div>
          <span className="mono-caption text-muted">
            REF: MAD-{property.id.slice(0, 4).toUpperCase()} · EXPEDIENTE ARRENDIS
          </span>
        </div>
      </div>

      {/* 3. Columna Derecha: Indicadores Técnicos y Acción Directa */}
      <div className="property-dossier-meta-col">
        <div className="property-dossier-indicators">
          <div className="dossier-indicator">
            <span className="dossier-indicator__label">SUMINISTROS CUPS</span>
            <span className="dossier-indicator__value">
              <Zap size={13} style={{ color: cupsCount > 0 ? 'var(--brand-burgundy)' : 'var(--text-muted)' }} />
              <span>{cupsCount > 0 ? `${cupsCount} contadores vinculados` : 'Pendiente vincular'}</span>
            </span>
          </div>

          <div className="dossier-indicator">
            <span className="dossier-indicator__label">DATOS CATASTRALES (IRPF)</span>
            <span className="dossier-indicator__value">
              {property.has_fiscal_data ? (
                <>
                  <CheckCircle2 size={13} style={{ color: 'var(--success)' }} />
                  <span>Modelo 100 y 3% listo</span>
                </>
              ) : (
                <>
                  <FileText size={13} style={{ color: 'var(--text-muted)' }} />
                  <span>Sin amortización</span>
                </>
              )}
            </span>
          </div>
        </div>

        <div className="property-dossier-action">
          <span className="btn btn-secondary btn-sm" style={{ width: '100%', justifyContent: 'center' }}>
            <span>Abrir Expediente</span>
            <ArrowRight size={13} style={{ marginLeft: '0.4rem' }} />
          </span>
        </div>
      </div>
    </article>
  );
}
