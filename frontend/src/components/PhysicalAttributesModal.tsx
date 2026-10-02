import { useState, useEffect } from "react";
import Modal from "./Modal";
import { updatePhysicalAttributes } from "../services/api";
import type { Property, PropertyCondition } from "../types";

interface PhysicalAttributesModalProps {
  isOpen: boolean;
  onClose: () => void;
  property: Property;
  onSuccess: (updatedProperty: Property) => void;
}

export default function PhysicalAttributesModal({
  isOpen,
  onClose,
  property,
  onSuccess,
}: PhysicalAttributesModalProps) {
  const [surfaceM2, setSurfaceM2] = useState<number | "">("");
  const [bedrooms, setBedrooms] = useState<number | "">("");
  const [bathrooms, setBathrooms] = useState<number | "">("");
  const [floor, setFloor] = useState<number | "">("");
  const [hasElevator, setHasElevator] = useState<boolean | "">("");
  const [condition, setCondition] = useState<PropertyCondition | "">("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setSurfaceM2(property.surface_m2 ?? "");
      setBedrooms(property.bedrooms ?? "");
      setBathrooms(property.bathrooms ?? "");
      setFloor(property.floor ?? "");
      setHasElevator(property.has_elevator !== undefined && property.has_elevator !== null ? property.has_elevator : "");
      setCondition(property.condition || "");
      setError(null);
    }
  }, [isOpen, property]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (surfaceM2 === "" || surfaceM2 <= 0) {
      setError("La superficie construida en m² es obligatoria y debe ser mayor que cero.");
      return;
    }

    setSaving(true);
    try {
      const updated = await updatePhysicalAttributes(property.id, {
        surface_m2: Number(surfaceM2),
        bedrooms: bedrooms !== "" ? Number(bedrooms) : undefined,
        bathrooms: bathrooms !== "" ? Number(bathrooms) : undefined,
        floor: floor !== "" ? Number(floor) : undefined,
        has_elevator: hasElevator !== "" ? Boolean(hasElevator) : undefined,
        condition: condition !== "" ? (condition as PropertyCondition) : undefined,
      });
      onSuccess(updated);
      onClose();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al actualizar las características físicas";
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Características Físicas del Inmueble">
      <form onSubmit={handleSubmit} className="physical-attributes-form">
        <div className="modal-intro-text">
          <p style={{ margin: "0 0 16px", color: "var(--text-secondary, #64748b)", fontSize: "0.875rem" }}>
            Los atributos físicos permiten al motor de inteligencia inmobiliaria contrastar tu propiedad con testigos reales de la zona con máxima precisión.
          </p>
        </div>

        {error && (
          <div className="error-banner" style={{ marginBottom: "16px" }}>
            {error}
          </div>
        )}

        <div className="form-group" style={{ marginBottom: "14px" }}>
          <label htmlFor="surface_m2">Superficie construida (m²) *</label>
          <input
            id="surface_m2"
            type="number"
            min="1"
            max="10000"
            value={surfaceM2}
            onChange={(e) => setSurfaceM2(e.target.value === "" ? "" : Number(e.target.value))}
            placeholder="Ej: 85"
            required
            className="form-input"
          />
        </div>

        <div className="form-row" style={{ marginBottom: "14px" }}>
          <div className="form-group">
            <label htmlFor="bedrooms">Dormitorios</label>
            <input
              id="bedrooms"
              type="number"
              min="0"
              max="50"
              value={bedrooms}
              onChange={(e) => setBedrooms(e.target.value === "" ? "" : Number(e.target.value))}
              placeholder="0 (estudio), 1, 2..."
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="bathrooms">Baños</label>
            <input
              id="bathrooms"
              type="number"
              min="0"
              max="20"
              value={bathrooms}
              onChange={(e) => setBathrooms(e.target.value === "" ? "" : Number(e.target.value))}
              placeholder="1, 2..."
              className="form-input"
            />
          </div>
        </div>

        <div className="form-row" style={{ marginBottom: "14px" }}>
          <div className="form-group">
            <label htmlFor="floor">Planta</label>
            <input
              id="floor"
              type="number"
              min="-3"
              max="100"
              value={floor}
              onChange={(e) => setFloor(e.target.value === "" ? "" : Number(e.target.value))}
              placeholder="Ej: 3 (bajo = 0)"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="has_elevator">¿Dispone de ascensor?</label>
            <select
              id="has_elevator"
              value={hasElevator === "" ? "" : hasElevator ? "true" : "false"}
              onChange={(e) => setHasElevator(e.target.value === "" ? "" : e.target.value === "true")}
              className="form-input"
            >
              <option value="">No especificado</option>
              <option value="true">Sí</option>
              <option value="false">No</option>
            </select>
          </div>
        </div>

        <div className="form-group" style={{ marginBottom: "20px" }}>
          <label htmlFor="condition">Estado de conservación</label>
          <select
            id="condition"
            value={condition}
            onChange={(e) => setCondition(e.target.value as PropertyCondition | "")}
            className="form-input"
          >
            <option value="">No especificado</option>
            <option value="a_reformar">A reformar</option>
            <option value="buen_estado">Buen estado</option>
            <option value="reformado">Reformado</option>
            <option value="a_estrenar">A estrenar</option>
          </select>
        </div>

        <div className="form-actions">
          <button type="button" onClick={onClose} className="btn btn-secondary" disabled={saving}>
            Cancelar
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Guardando..." : "Guardar características"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
