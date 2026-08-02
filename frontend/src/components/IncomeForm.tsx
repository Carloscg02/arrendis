import { useState } from "react";
import type { IncomeCreateInput, FiscalIncomeCategory } from "../types";

interface Props {
  propertyId: string;
  onSubmit: (data: IncomeCreateInput) => void;
  onCancel: () => void;
}

export default function IncomeForm({ propertyId, onSubmit, onCancel }: Props) {
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [category, setCategory] = useState("rent");
  const [description, setDescription] = useState("");
  const [fiscalCategory, setFiscalCategory] = useState<FiscalIncomeCategory | "">("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      property_id: propertyId,
      amount: parseFloat(amount),
      date,
      category,
      description,
      fiscal_category: fiscalCategory ? (fiscalCategory as FiscalIncomeCategory) : null,
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
        <label>Categoría</label>
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="rent">Alquiler</option>
          <option value="deposit">Fianza</option>
          <option value="other">Otro</option>
        </select>
      </div>

      <div className="form-group">
        <label>Descripción (Opcional)</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
        />
      </div>

      <div className="form-group">
        <label>Categoría Fiscal (Opcional)</label>
        <select value={fiscalCategory} onChange={(e) => setFiscalCategory(e.target.value as any)}>
          <option value="">Seleccione una categoría...</option>
          <option value="rendimiento_integro">Rendimiento Íntegro</option>
          <option value="indemnizacion">Indemnización</option>
          <option value="otros_ingresos">Otros Ingresos</option>
        </select>
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
