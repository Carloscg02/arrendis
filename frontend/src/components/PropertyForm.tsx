import { useState } from "react";
import type { PropertyCreateInput } from "../types";

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
