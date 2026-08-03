import { useState } from "react";
import type { IncomeCreateInput, FiscalIncomeCategory } from "../types";

interface Props {
  propertyId: string;
  onSubmit: (data: IncomeCreateInput) => void;
  onCancel: () => void;
}

interface CategoryMapping {
  label: string;
  category: string;
  fiscalCategory: FiscalIncomeCategory | null;
}

const INCOME_CATEGORIES: Record<string, CategoryMapping> = {
  rent: {
    label: "Renta de Alquiler (Rendimiento Íntegro Computable)",
    category: "rent",
    fiscalCategory: "rendimiento_integro",
  },
  deposit: {
    label: "Fianza / Depósito (Fianza recibida)",
    category: "deposit",
    fiscalCategory: null,
  },
  otros_ingresos: {
    label: "Otros Ingresos Computables (Indemnización, reexpedición)",
    category: "other",
    fiscalCategory: "otros_ingresos",
  },
};

export default function IncomeForm({ propertyId, onSubmit, onCancel }: Props) {
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [selectedCategoryKey, setSelectedCategoryKey] = useState("rent");
  const [description, setDescription] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const mapping = INCOME_CATEGORIES[selectedCategoryKey] || INCOME_CATEGORIES.rent;

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
        <label>Categoría del Ingreso</label>
        <select
          value={selectedCategoryKey}
          onChange={(e) => setSelectedCategoryKey(e.target.value)}
          required
        >
          {Object.entries(INCOME_CATEGORIES).map(([key, item]) => (
            <option key={key} value={key}>
              {item.label}
            </option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label>Descripción (Opcional)</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          placeholder="Ej: Alquiler mes de junio"
        />
      </div>

      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel}>
          Cancelar
        </button>
        <button type="submit" className="btn btn-primary">
          Registrar Ingreso
        </button>
      </div>
    </form>
  );
}
