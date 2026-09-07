import { useState } from "react";
import { Info } from "lucide-react";
import type { ExpenseCreateInput, FiscalExpenseCategory } from "../types";

interface Props {
  propertyId: string;
  onSubmit: (data: ExpenseCreateInput) => void;
  onCancel: () => void;
}

interface CategoryMapping {
  label: string;
  category: string;
  fiscalCategory: FiscalExpenseCategory | null;
}

const EXPENSE_CATEGORIES: Record<string, CategoryMapping> = {
  reparacion_conservacion: {
    label: "Reparación y Conservación (Pintura, averías, fontanería)",
    category: "repair",
    fiscalCategory: "reparacion_conservacion",
  },
  tributos: {
    label: "Tributos, Tasas y Recargos (IBI, tasa de basuras)",
    category: "tax",
    fiscalCategory: "tributos",
  },
  primas_seguros: {
    label: "Primas de Seguros (Hogar, impago de alquiler)",
    category: "insurance",
    fiscalCategory: "primas_seguros",
  },
  comunidad: {
    label: "Comunidad de Propietarios",
    category: "community_fee",
    fiscalCategory: "servicios_suministros",
  },
  servicios_suministros: {
    label: "Suministros (Agua, luz, gas, internet)",
    category: "utility",
    fiscalCategory: "servicios_suministros",
  },
  intereses_capital: {
    label: "Intereses de Hipoteca / Financiación",
    category: "mortgage",
    fiscalCategory: "intereses_capital",
  },
  formalizacion: {
    label: "Gastos de Formalización (Notaría, gestoría, contrato)",
    category: "other",
    fiscalCategory: "formalizacion",
  },
  dudoso_cobro: {
    label: "Saldos de Dudoso Cobro (Impagos justificados)",
    category: "other",
    fiscalCategory: "dudoso_cobro",
  },
  amortizacion_muebles: {
    label: "Compra de Bienes Muebles (10% anual: electrodomésticos, muebles)",
    category: "other",
    fiscalCategory: "amortizacion_muebles",
  },
  otros_deducibles: {
    label: "Otros Gastos Deducibles",
    category: "other",
    fiscalCategory: "otros_deducibles",
  },
  no_deducible: {
    label: "No Deducible (Gasto no deducible fiscalmente)",
    category: "other",
    fiscalCategory: "no_deducible",
  },
};

export default function ExpenseForm({ propertyId, onSubmit, onCancel }: Props) {
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [selectedCategoryKey, setSelectedCategoryKey] = useState("reparacion_conservacion");
  const [description, setDescription] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const mapping = EXPENSE_CATEGORIES[selectedCategoryKey] || EXPENSE_CATEGORIES.reparacion_conservacion;

    onSubmit({
      property_id: propertyId,
      amount: parseFloat(amount),
      date,
      category: mapping.category,
      description,
      fiscal_category: mapping.fiscalCategory,
    });
  };

  return (
    <form className="form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label>Importe (€)</label>
        <input
          type="number"
          step="0.01"
          min="0"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          required
          placeholder="0.00"
        />
      </div>

      <div className="form-group">
        <label>Fecha</label>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          required
        />
      </div>

      <div className="form-group">
        <label>Categoría del Gasto</label>
        <select
          value={selectedCategoryKey}
          onChange={(e) => setSelectedCategoryKey(e.target.value)}
          required
        >
          {Object.entries(EXPENSE_CATEGORIES).map(([key, item]) => (
            <option key={key} value={key}>
              {item.label}
            </option>
          ))}
        </select>
      </div>

      {selectedCategoryKey === "dudoso_cobro" && (
        <div className="report-warning" style={{ fontSize: "0.85rem" }}>
          <Info size={15} style={{ display: 'inline', verticalAlign: '-2px', marginRight: '0.4rem' }} />
          <strong>Requisito legal:</strong> Para deducir impagos como saldos de dudoso cobro,
          deben haber transcurrido más de 6 meses desde la primera gestión de cobro,
          o el deudor debe estar en situación de concurso de acreedores (Art. 13 RIRPF).
        </div>
      )}

      <div className="form-group">
        <label>Descripción (Opcional)</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          placeholder="Ej: Reparación de fuga en baño"
        />
      </div>

      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel}>
          Cancelar
        </button>
        <button type="submit" className="btn btn-danger">
          Registrar Gasto
        </button>
      </div>
    </form>
  );
}
