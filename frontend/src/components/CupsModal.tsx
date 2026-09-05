import { useState, useEffect } from "react";
import { Info } from "lucide-react";
import Modal from "./Modal";
import { updatePropertyCups } from "../services/api";

interface CupsModalProps {
  isOpen: boolean;
  onClose: () => void;
  propertyId: string;
  initialCups: {
    cups_electricity?: string | null;
    cups_gas?: string | null;
    cups_water?: string | null;
  };
  onSuccess: () => void;
}

export default function CupsModal({
  isOpen,
  onClose,
  propertyId,
  initialCups,
  onSuccess,
}: CupsModalProps) {
  const [cupsElectricity, setCupsElectricity] = useState("");
  const [cupsGas, setCupsGas] = useState("");
  const [cupsWater, setCupsWater] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setCupsElectricity(initialCups.cups_electricity || "");
      setCupsGas(initialCups.cups_gas || "");
      setCupsWater(initialCups.cups_water || "");
      setError(null);
    }
  }, [isOpen, initialCups]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    const cleanElec = cupsElectricity.trim().toUpperCase() || null;
    const cleanGas = cupsGas.trim().toUpperCase() || null;
    const cleanWater = cupsWater.trim().toUpperCase() || null;

    try {
      await updatePropertyCups(propertyId, {
        cups_electricity: cleanElec,
        cups_gas: cleanGas,
        cups_water: cleanWater,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || "Error al actualizar los códigos CUPS.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Suministros y Códigos CUPS">
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        <div
          style={{
            padding: "0.75rem 1rem",
            backgroundColor: "var(--bg-tertiary)",
            borderRadius: "var(--radius-md)",
            fontSize: "0.85rem",
            color: "var(--text-secondary)",
            display: "flex",
            gap: "0.6rem",
            alignItems: "flex-start",
          }}
        >
          <Info size={16} style={{ flexShrink: 0, marginTop: "2px", color: "var(--accent-secondary)" }} />
          <span>
            El <strong>CUPS</strong> (Código Unificado de Punto de Suministro) identifica de forma única tu contador. Al configurarlo, cualquier factura PDF que subas se vinculará de manera automática a este inmueble.
          </span>
        </div>

        {error && (
          <div
            style={{
              padding: "0.75rem 1rem",
              backgroundColor: "var(--toast-error-bg)",
              border: "1px solid #fecaca",
              borderRadius: "var(--radius-md)",
              color: "var(--danger)",
              fontSize: "0.85rem",
            }}
          >
            {error}
          </div>
        )}

        <div className="form-group">
          <label>CUPS Electricidad (Luz)</label>
          <input
            type="text"
            value={cupsElectricity}
            onChange={(e) => setCupsElectricity(e.target.value.toUpperCase())}
            placeholder="ES0031103721971011PR0F"
            style={{ textTransform: "uppercase", letterSpacing: "0.05em", fontFamily: "monospace" }}
          />
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
            20 o 22 caracteres (empieza por ES). Lo encuentras en el encabezado de tu factura de luz.
          </span>
        </div>

        <div className="form-group">
          <label>CUPS Gas (Opcional)</label>
          <input
            type="text"
            value={cupsGas}
            onChange={(e) => setCupsGas(e.target.value.toUpperCase())}
            placeholder="ES0201..."
            style={{ textTransform: "uppercase", letterSpacing: "0.05em", fontFamily: "monospace" }}
          />
        </div>

        <div className="form-group">
          <label>CUPS o Nº Contador Agua (Opcional)</label>
          <input
            type="text"
            value={cupsWater}
            onChange={(e) => setCupsWater(e.target.value.toUpperCase())}
            placeholder="ES..."
            style={{ textTransform: "uppercase", letterSpacing: "0.05em", fontFamily: "monospace" }}
          />
        </div>

        <div className="form-actions" style={{ marginTop: "0.5rem" }}>
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>
            Cancelar
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Guardando..." : "Guardar CUPS"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
