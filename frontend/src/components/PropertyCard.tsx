import { useNavigate } from "react-router-dom";
import { Building2, MapPin, ChevronRight } from "lucide-react";
import type { Property } from "../types";

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
      case "apartment": return "Apartamento";
      case "house": return "Casa";
      case "commercial": return "Local Comercial";
      case "garage": return "Garaje";
      case "land": return "Terreno";
      default: return type;
    }
  };

  return (
    <div
      className="property-card"
      onClick={() => navigate(`/properties/${property.id}`)}
    >
      <div 
        className={`property-card-image ${!property.image_url ? 'property-card-placeholder' : ''}`}
        style={property.image_url ? { backgroundImage: `url(http://localhost:8000${property.image_url})` } : undefined}
      >
        {!property.image_url && (
          <Building2 size={32} strokeWidth={1.5} className="property-card-placeholder-icon" />
        )}
      </div>
      <div className="property-card-content">
        <div className="property-card-header">
          <h3 className="property-name">{property.name}</h3>
          <span className={`badge ${getStatusClass(property.status)}`}>
            {translateStatus(property.status)}
          </span>
        </div>
        <p className="property-address">
          <MapPin size={13} style={{ marginRight: '0.35rem', verticalAlign: '-1px', flexShrink: 0 }} />
          <span>{property.address.street}, {property.address.city} {property.address.postal_code}</span>
        </p>
        <div className="property-card-footer">
          <span className="badge badge-outline">{translateType(property.property_type)}</span>
          <span className="property-card-cta">
            Ver detalle <ChevronRight size={14} />
          </span>
        </div>
      </div>
    </div>
  );
}
