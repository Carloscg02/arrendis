import { useState } from "react";
import { getFiscalSuggestions, updateIncomeFiscalCategory, updateExpenseFiscalCategory } from "../services/api";
import type { FiscalSuggestionsResponse } from "../types";
import { useToast } from "./Toast";

interface Props {
  propertyId: string;
  onClassified: () => void;
}

export default function FiscalClassificationPanel({ propertyId, onClassified }: Props) {
  const [suggestions, setSuggestions] = useState<FiscalSuggestionsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const toast = useToast();

  const handleGetSuggestions = async () => {
    try {
      setLoading(true);
      const data = await getFiscalSuggestions(propertyId);
      setSuggestions(data);
    } catch (error: any) {
      toast.error(error.message || "Error al obtener sugerencias");
    } finally {
      setLoading(false);
    }
  };

  const handleApplyAll = async () => {
    if (!suggestions) return;
    try {
      setApplying(true);
      const incomePromises = suggestions.unclassified_incomes.map(inc =>
        updateIncomeFiscalCategory(inc.id, inc.suggested_fiscal_category)
      );
      const expensePromises = suggestions.unclassified_expenses.map(exp =>
        updateExpenseFiscalCategory(exp.id, exp.suggested_fiscal_category)
      );
      await Promise.all([...incomePromises, ...expensePromises]);
      toast.success("Categorías fiscales aplicadas correctamente");
      setSuggestions(null);
      onClassified();
    } catch (error: any) {
      toast.error(error.message || "Error al aplicar categorías");
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="fiscal-classification-panel" style={{ marginTop: '2rem', padding: '1.5rem', border: '1px solid var(--panel-border)', borderRadius: 'var(--radius-lg)', background: 'var(--panel-bg)' }}>
      <h3>Clasificación Fiscal Inteligente</h3>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
        Analiza tus ingresos y gastos para sugerir la categoría fiscal correspondiente según la AEAT.
      </p>
      
      {!suggestions ? (
        <button className="btn btn-primary" onClick={handleGetSuggestions} disabled={loading}>
          {loading ? "Analizando..." : "Generar Sugerencias"}
        </button>
      ) : (
        <div className="suggestions-results">
          {suggestions.total_unclassified === 0 ? (
            <p style={{ color: 'var(--text-secondary)' }}>Todos los movimientos están clasificados fiscalmente. ¡Buen trabajo!</p>
          ) : (
            <>
              <p style={{ color: 'var(--text-primary)', fontWeight: 500 }}>Se han encontrado {suggestions.total_unclassified} movimientos sin clasificar.</p>
              
              {suggestions.unclassified_incomes.length > 0 && (
                <div className="suggestion-group" style={{ marginTop: '1rem' }}>
                  <h4>Ingresos</h4>
                  <ul style={{ listStyle: 'none', padding: 0 }}>
                    {suggestions.unclassified_incomes.map(inc => (
                      <li key={inc.id} style={{ padding: '0.75rem', background: 'var(--bg-tertiary)', marginBottom: '0.5rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--panel-border)' }}>
                        {inc.description || inc.category} ({inc.amount} €) 
                        <span className="arrow" style={{ margin: '0 0.5rem' }}> → </span> 
                        <span className="badge badge-success">{inc.suggested_fiscal_category}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {suggestions.unclassified_expenses.length > 0 && (
                <div className="suggestion-group" style={{ marginTop: '1rem' }}>
                  <h4>Gastos</h4>
                  <ul style={{ listStyle: 'none', padding: 0 }}>
                    {suggestions.unclassified_expenses.map(exp => (
                      <li key={exp.id} style={{ padding: '0.75rem', background: 'var(--bg-tertiary)', marginBottom: '0.5rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--panel-border)' }}>
                        {exp.description || exp.category} ({exp.amount} €) 
                        <span className="arrow" style={{ margin: '0 0.5rem' }}> → </span> 
                        <span className="badge badge-neutral">{exp.suggested_fiscal_category}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="form-actions" style={{ marginTop: '1rem' }}>
                <button className="btn btn-secondary" onClick={() => setSuggestions(null)} disabled={applying}>
                  Cancelar
                </button>
                <button className="btn btn-primary" onClick={handleApplyAll} disabled={applying}>
                  {applying ? "Aplicando..." : "Aplicar Todas las Sugerencias"}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
