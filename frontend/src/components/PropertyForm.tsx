import { useState } from "react";
import type { PropertyCreateInput, PropertyCondition } from "../types";

interface Props {
  onSubmit: (data: PropertyCreateInput) => void;
  onCancel: () => void;
}

export default function PropertyForm({ onSubmit, onCancel }: Props) {
  const [name, setName] = useState("");
  const [street, setStreet] = useState("");
  const [city, setCity] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [country, setCountry] = useState("ES");
  const [propertyType, setPropertyType] = useState("apartment");
  const [surfaceM2, setSurfaceM2] = useState<string>("");
  const [bedrooms, setBedrooms] = useState<string>("");
  const [bathrooms, setBathrooms] = useState<string>("");
  const [floor, setFloor] = useState<string>("");
  const [hasElevator, setHasElevator] = useState<boolean>(false);
  const [condition, setCondition] = useState<PropertyCondition | "">("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      name,
      address: {
        street,
        city,
        postal_code: postalCode,
        country,
      },
      property_type: propertyType,
      surface_m2: surfaceM2 ? parseInt(surfaceM2, 10) : null,
      bedrooms: bedrooms ? parseInt(bedrooms, 10) : null,
      bathrooms: bathrooms ? parseInt(bathrooms, 10) : null,
      floor: floor !== "" ? parseInt(floor, 10) : null,
      has_elevator: hasElevator,
      condition: condition || null,
    });
  };

  return (
    <form className="form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label>Nombre de la Propiedad</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          placeholder="ej., Piso en el Centro"
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Calle</label>
          <input
            type="text"
            value={street}
            onChange={(e) => setStreet(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label>Ciudad</label>
          <input
            type="text"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            required
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Código Postal</label>
          <input
            type="text"
            value={postalCode}
            onChange={(e) => setPostalCode(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label>País</label>
          <input
            type="text"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            required
          />
        </div>
      </div>

      <div className="form-group">
        <label>Tipo de Propiedad</label>
        <select
          value={propertyType}
          onChange={(e) => setPropertyType(e.target.value)}
        >
          <option value="apartment">Apartamento</option>
          <option value="house">Casa</option>
          <option value="commercial">Local Comercial</option>
          <option value="land">Terreno</option>
          <option value="other">Otro</option>
        </select>
      </div>

      <div style={{ borderTop: "1px solid var(--panel-border, #e8e4de)", paddingTop: "1rem", marginTop: "1.25rem" }}>
        <p style={{
          fontSize: "0.72rem",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          color: "var(--text-muted, #8c827a)",
          fontFamily: "var(--font-mono)",
          margin: "0 0 0.75rem 0",
        }}>
          Características Físicas (Opcional — para valoración de mercado)
        </p>
        <div className="form-row">
          <div className="form-group">
            <label>Superficie (m²)</label>
            <input
              type="number"
              min="1"
              value={surfaceM2}
              onChange={(e) => setSurfaceM2(e.target.value)}
              placeholder="ej., 85"
            />
          </div>
          <div className="form-group">
            <label>Habitaciones</label>
            <input
              type="number"
              min="0"
              value={bedrooms}
              onChange={(e) => setBedrooms(e.target.value)}
              placeholder="ej., 2"
            />
          </div>
          <div className="form-group">
            <label>Baños</label>
            <input
              type="number"
              min="0"
              value={bathrooms}
              onChange={(e) => setBathrooms(e.target.value)}
              placeholder="ej., 1"
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Planta</label>
            <input
              type="number"
              value={floor}
              onChange={(e) => setFloor(e.target.value)}
              placeholder="ej., 3"
            />
          </div>
          <div className="form-group">
            <label>Estado de conservación</label>
            <select
              value={condition}
              onChange={(e) => setCondition(e.target.value as PropertyCondition | "")}
            >
              <option value="">No especificado</option>
              <option value="a_reformar">A reformar</option>
              <option value="buen_estado">Buen estado</option>
              <option value="reformado">Reformado</option>
              <option value="a_estrenar">A estrenar</option>
            </select>
          </div>
        </div>

        <div className="form-checkbox-group" style={{ marginTop: "0.85rem", marginBottom: "0.25rem" }}>
          <label
            className="form-checkbox-label"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.55rem",
              cursor: "pointer",
              marginBottom: 0,
              textTransform: "none",
              fontFamily: "var(--font-sans)",
              fontSize: "0.88rem",
              fontWeight: 500,
              color: "var(--text-primary, #2c2623)",
              letterSpacing: "normal",
              userSelect: "none",
            }}
          >
            <input
              type="checkbox"
              checked={hasElevator}
              onChange={(e) => setHasElevator(e.target.checked)}
              style={{
                width: "1.15rem",
                height: "1.15rem",
                margin: 0,
                padding: 0,
                accentColor: "var(--brand-burgundy, #6b0008)",
                cursor: "pointer",
                flexShrink: 0,
              }}
            />
            <span>Dispone de ascensor</span>
          </label>
        </div>
      </div>

      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel}>
          Cancelar
        </button>
        <button type="submit" className="btn btn-primary">
          Crear Propiedad
        </button>
      </div>
    </form>
  );
}
