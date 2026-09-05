import { useState } from "react";
import { Sparkles, ArrowRight } from "lucide-react";
import { getFiscalSuggestions, updateIncomeFiscalCategory, updateExpenseFiscalCategory } from "../services/api";
import type { FiscalSuggestionsResponse } from "../types";
import { useToast } from "./Toast";
import { 
  translateIncomeCategory, 
  translateExpenseCategory, 
  translateFiscalCategory 
} from "../utils/translations";

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
    <div className="fiscal-classification-panel">
      <div className="section-header" style={{ marginBottom: "1rem" }}>
        <h3>Clasificación Fiscal Inteligente</h3>
        {!suggestions && (
          <button className="btn btn-sm btn-primary" onClick={handleGetSuggestions} disabled={loading}>
            <Sparkles size={14} style={{ marginRight: "0.35rem" }} />
            {loading ? "Analizando..." : "Generar Sugerencias"}
          </button>
        )}
      </div>
      
      {suggestions && (
        <div className="suggestions-results">
          {suggestions.total_unclassified === 0 ? (
            <p className="empty-text">Todos los movimientos están clasificados fiscalmente.</p>
          ) : (
            <>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1rem' }}>
                Se han encontrado <strong style={{ color: 'var(--text-primary)' }}>{suggestions.total_unclassified}</strong> movimientos pendientes de clasificar:
              </p>
              
              {suggestions.unclassified_incomes.length > 0 && (
                <div className="suggestion-group">
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 500, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.5rem' }}>Ingresos</h4>
                  <ul className="suggestion-list">
                    {suggestions.unclassified_incomes.map(inc => (
                      <li key={inc.id} className="suggestion-item">
                        <span>{inc.description || translateIncomeCategory(inc.category)} ({inc.amount} €)</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <ArrowRight size={14} style={{ color: 'var(--text-muted)' }} />
                          <span className="badge badge-success">{translateFiscalCategory(inc.suggested_fiscal_category)}</span>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {suggestions.unclassified_expenses.length > 0 && (
                <div className="suggestion-group" style={{ marginTop: '1.25rem' }}>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 500, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.5rem' }}>Gastos</h4>
                  <ul className="suggestion-list">
                    {suggestions.unclassified_expenses.map(exp => (
                      <li key={exp.id} className="suggestion-item">
                        <span>{exp.description || translateExpenseCategory(exp.category)} ({exp.amount} €)</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <ArrowRight size={14} style={{ color: 'var(--text-muted)' }} />
                          <span className="badge badge-neutral">{translateFiscalCategory(exp.suggested_fiscal_category)}</span>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="form-actions" style={{ marginTop: '1.5rem' }}>
                <button className="btn btn-secondary btn-sm" onClick={() => setSuggestions(null)} disabled={applying}>
                  Cancelar
                </button>
                <button className="btn btn-primary btn-sm" onClick={handleApplyAll} disabled={applying}>
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
