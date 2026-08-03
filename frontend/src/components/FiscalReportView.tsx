import { useState } from "react";
import type { FiscalReport } from "../types";
import { getFiscalReport, downloadFiscalReportPdf } from "../services/api";
import { useToast } from "./Toast";
import { SkeletonLoader } from "./SkeletonLoader";

interface Props {
  propertyId: string;
}

export default function FiscalReportView({ propertyId }: Props) {
  const [year, setYear] = useState(new Date().getFullYear());
  const [report, setReport] = useState<FiscalReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const toast = useToast();

  const handleGenerate = async () => {
    try {
      setLoading(true);
      const data = await getFiscalReport(propertyId, year);
      setReport(data);
    } catch (error: any) {
      toast.error(error.message || "Error al generar el informe fiscal");
      setReport(null);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = async () => {
    try {
      setDownloading(true);
      await downloadFiscalReportPdf(propertyId, year);
    } catch (error: any) {
      toast.error(error.message || "Error al descargar el PDF");
    } finally {
      setDownloading(false);
    }
  };

  const years = [2026, 2025, 2024, 2023, 2022, 2021, 2020];

  return (
    <div className="fiscal-report-container">
      <div className="fiscal-report-header">
        <h2>Motor de Cálculo Fiscal (IRPF)</h2>
        <div className="fiscal-report-controls">
          <select 
            value={year} 
            onChange={(e) => setYear(Number(e.target.value))}
            style={{ width: "auto" }}
          >
            {years.map(y => <option key={y} value={y}>{y}</option>)}
          </select>
          <button className="btn btn-primary" onClick={handleGenerate} disabled={loading}>
            {loading ? "Generando..." : "Generar Informe"}
          </button>
        </div>
      </div>

      {loading && <SkeletonLoader variant="kpi" count={1} />}

      {!loading && report && (
        <div className="report-content">
          {report.has_warnings && (
            <div className="report-warning">
              <strong>⚠️ Advertencia:</strong> Tienes {report.unclassified_income_count} ingreso(s) y {report.unclassified_expense_count} gasto(s) sin clasificar. 
              Clasifícalos para asegurar un cálculo preciso.
            </div>
          )}

          {/* Sección 1: Rendimientos Íntegros */}
          <div className="report-section">
            <div className="report-section-header">📊 1. Rendimientos Íntegros</div>
            <div className="report-row">
              <span>Ingresos por Alquiler</span>
              <span>{parseFloat(report.gross_rental_income).toFixed(2)} €</span>
            </div>
            <div className="report-row">
              <span>Otros Ingresos</span>
              <span>{parseFloat(report.other_income).toFixed(2)} €</span>
            </div>
            <div className="report-row total">
              <span>Total Rendimientos Íntegros</span>
              <span className="text-success">{parseFloat(report.total_income).toFixed(2)} €</span>
            </div>
          </div>

          {/* Sección 2: Ocupación */}
          <div className="report-section">
            <div className="report-section-header">🏠 2. Ocupación (Prorrateo)</div>
            <p>La vivienda estuvo alquilada <strong>{report.rented_days}</strong> días de {report.total_days_in_year}. Ratio de ocupación: {(parseFloat(report.occupation_ratio) * 100).toFixed(2)}%.</p>
            <div className="occupation-bar-container">
              <div 
                className="occupation-bar-fill" 
                style={{ width: `${parseFloat(report.occupation_ratio) * 100}%` }}
              ></div>
            </div>
            <p className="text-secondary" style={{ fontSize: "0.85rem" }}>Los gastos fijos se prorratearán según este ratio.</p>
          </div>

          {/* Sección 3: Gastos Deducibles */}
          <div className="report-section">
            <div className="report-section-header">💰 3. Gastos Deducibles (Prorrateados)</div>
            <div className="report-row">
              <span>Intereses de Capital</span>
              <span>{parseFloat(report.expenses_intereses).toFixed(2)} €</span>
            </div>
            <div className="report-row">
              <span>Reparación y Conservación</span>
              <span>{parseFloat(report.expenses_reparacion).toFixed(2)} €</span>
            </div>
            
            <div className="report-row" style={{ marginTop: "1rem" }}>
              <span>Tributos (IBI, Tasas, etc.)</span>
              <span>{parseFloat(report.expenses_tributos).toFixed(2)} €</span>
            </div>
            <div className="report-row">
              <span>Primas de Seguros</span>
              <span>{parseFloat(report.expenses_seguros).toFixed(2)} €</span>
            </div>
            <div className="report-row">
              <span>Suministros</span>
              <span>{parseFloat(report.expenses_suministros).toFixed(2)} €</span>
            </div>
            <div className="report-row">
              <span>Formalización Contratos</span>
              <span>{parseFloat(report.expenses_formalizacion).toFixed(2)} €</span>
            </div>
            <div className="report-row">
              <span>Saldos de Dudoso Cobro</span>
              <span>{parseFloat(report.expenses_dudoso_cobro).toFixed(2)} €</span>
            </div>
            <div className="report-row">
              <span>Otros Gastos</span>
              <span>{parseFloat(report.expenses_otros).toFixed(2)} €</span>
            </div>
          </div>

          {/* Sección 4: Tope de Reparación e Intereses */}
          <div className="report-section">
            <div className="report-section-header">⚠️ 4. Tope Art. 23.1.a LIRPF</div>
            <p className="text-secondary mb-2" style={{ fontSize: "0.85rem" }}>Los gastos de reparación e intereses no pueden superar los rendimientos íntegros.</p>
            <div className="report-row">
              <span>Total Reparación + Intereses (Bruto)</span>
              <span>{parseFloat(report.repair_interest_raw).toFixed(2)} €</span>
            </div>
            <div className="report-row">
              <span>Límite (Rendimientos Íntegros)</span>
              <span>{parseFloat(report.repair_interest_cap).toFixed(2)} €</span>
            </div>
            <div className="report-row total">
              <span>Gasto Aplicable</span>
              <span>{parseFloat(report.repair_interest_applied).toFixed(2)} €</span>
            </div>
            {parseFloat(report.repair_interest_excess) > 0 && (
              <div className="report-row text-danger mt-4">
                <span>Exceso pendiente para 4 años</span>
                <span>{parseFloat(report.repair_interest_excess).toFixed(2)} €</span>
              </div>
            )}
          </div>

          {/* Sección 5: Amortización */}
          <div className="report-section">
            <div className="report-section-header">🏗️ 5. Amortización del Inmueble</div>
            <div className="report-row">
              <span>Base de Amortización (Mayor Const. vs Catastro)</span>
              <span>{parseFloat(report.amortization_base).toFixed(2)} €</span>
            </div>
            <div className="report-row">
              <span>Tipo (%)</span>
              <span>{(parseFloat(report.amortization_rate) * 100).toFixed(2)}%</span>
            </div>
            <div className="report-row">
              <span>Amortización Anual Completa</span>
              <span>{parseFloat(report.amortization_full_year).toFixed(2)} €</span>
            </div>
            <div className="report-row total">
              <span>Amortización Prorrateada (Aplicable)</span>
              <span>{parseFloat(report.amortization_prorated).toFixed(2)} €</span>
            </div>
          </div>

          {/* Sección 6: Rendimiento Neto Previo */}
          <div className="report-section" style={{ border: "2px solid var(--panel-border)" }}>
            <div className="report-section-header">📋 6. Rendimiento Neto Previo</div>
            <div className="report-row">
              <span>Total Rendimientos Íntegros</span>
              <span>{parseFloat(report.total_income).toFixed(2)} €</span>
            </div>
            <div className="report-row">
              <span>Total Gastos Deducibles (Incl. Amort.)</span>
              <span className="text-danger">-{parseFloat(report.total_deductible_expenses).toFixed(2)} €</span>
            </div>
            <div className="report-row total" style={{ fontSize: "1.3rem" }}>
              <span>Rendimiento Neto (Previo Reducciones)</span>
              <span>{parseFloat(report.net_income_before_reduction).toFixed(2)} €</span>
            </div>
          </div>

          {/* Sección 7: Reducción Vivienda Habitual */}
          <div className="report-section">
            <div className="report-section-header">🏡 7. Reducción Vivienda Habitual (60%)</div>
            <div className="report-row">
              <span>Días como Vivienda Habitual</span>
              <span>{report.vivienda_habitual_days}</span>
            </div>
            <div className="report-row">
              <span>Ratio sobre días alquilados</span>
              <span>{(parseFloat(report.vivienda_habitual_ratio) * 100).toFixed(2)}%</span>
            </div>
            <div className="report-row">
              <span>Base de Reducción</span>
              <span>{parseFloat(report.reduction_base).toFixed(2)} €</span>
            </div>
            <div className="report-row total">
              <span>Importe Reducción Aplicable</span>
              <span className="text-success">-{parseFloat(report.reduction_amount).toFixed(2)} €</span>
            </div>
          </div>

          {/* Sección 8: Resultado Final */}
          <div className="final-result-card">
            <div className="report-section-header" style={{ justifyContent: "center", marginBottom: "0" }}>
              ✅ 8. Rendimiento Neto Reducido
            </div>
            <p className="text-secondary">Este es el importe final a declarar en el IRPF</p>
            <div className="final-result-value">
              {parseFloat(report.net_income_final).toFixed(2)} €
            </div>
          </div>

          {/* Sección 9: Descarga PDF */}
          <div className="fiscal-report-download-section">
            <button
              className="fiscal-report-download-btn"
              onClick={handleDownloadPdf}
              disabled={downloading}
            >
              {downloading ? (
                <>
                  <span className="fiscal-report-download-spinner" />
                  Generando PDF...
                </>
              ) : (
                <>📄 Descargar Borrador Fiscal (PDF)</>
              )}
            </button>
            <p className="fiscal-report-download-disclaimer">
              Este documento es un borrador orientativo. Los datos deben trasladarse
              manualmente a Renta Web (AEAT).
            </p>
          </div>

        </div>
      )}
    </div>
  );
}

