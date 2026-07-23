import { useNavigate } from "react-router-dom";
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
      case "apartment": return "🏢 Apartamento";
      case "house": return "🏠 Casa";
      case "commercial": return "🏪 Local Comercial";
      case "garage": return "🚗 Garaje";
      case "land": return "🌍 Terreno";
      default: return `🏗️ ${type}`;
    }
  };

  const getTypeEmoji = (type: string) => {
    switch (type.toLowerCase()) {
      case "apartment": return "🏢";
      case "house": return "🏠";
      case "commercial": return "🏪";
      case "garage": return "🚗";
      case "land": return "🌍";
      default: return "🏗️";
    }
  };

  return (
    <div
      className="property-card glass-panel"
      onClick={() => navigate(`/properties/${property.id}`)}
    >
      <div 
        className={`property-card-image ${!property.image_url ? 'property-card-placeholder' : ''}`}
        style={property.image_url ? { backgroundImage: `url(http://localhost:8000${property.image_url})` } : undefined}
      >
        {!property.image_url && (
          <span className="property-card-placeholder-icon">{getTypeEmoji(property.property_type)}</span>
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
          📍 {property.address.street}, {property.address.city}{" "}
          {property.address.postal_code}
        </p>
        <span className="badge badge-outline">{translateType(property.property_type)}</span>
      </div>
    </div>
  );
}
