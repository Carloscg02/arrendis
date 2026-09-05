import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { 
  ArrowLeft, 
  Upload, 
  Trash2, 
  TrendingUp, 
  TrendingDown, 
  Scale, 
  Wallet, 
  FileText, 
  ReceiptText, 
  Plus,
  ChevronRight,
  UploadCloud,
  SlidersHorizontal
} from "lucide-react";
import { translateIncomeCategory, translateExpenseCategory } from "../utils/translations";
import type {
  Property,
  Income,
  Expense,
  ProfitReport,
  IncomeCreateInput,
  ExpenseCreateInput,
  FiscalDataInput,
} from "../types";
import {
  getPropertyById,
  getIncomes,
  getExpenses,
  getProfitReport,
  createIncome,
  deleteIncome,
  createExpense,
  deleteExpense,
  deleteProperty,
  uploadPropertyImage,
  updateFiscalData,
} from "../services/api";
import IncomeForm from "../components/IncomeForm";
import ExpenseForm from "../components/ExpenseForm";
import FiscalDataForm from "../components/FiscalDataForm";
import FiscalClassificationPanel from "../components/FiscalClassificationPanel";
import FiscalReportView from "../components/FiscalReportView";
import { ContractSection } from "../components/ContractSection";
import Modal from "../components/Modal";
import InvoiceUploadModal from "../components/InvoiceUploadModal";
import CupsModal from "../components/CupsModal";
import { useToast } from "../components/Toast";
import { KPICard } from "../components/KPICard";
import { SkeletonLoader } from "../components/SkeletonLoader";
import { ConfirmDialog } from "../components/ConfirmDialog";

export default function PropertyDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();

  const [property, setProperty] = useState<Property | null>(null);
  const [incomes, setIncomes] = useState<Income[]>([]);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [profit, setProfit] = useState<ProfitReport | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const [isIncomeModalOpen, setIsIncomeModalOpen] = useState(false);
  const [isExpenseModalOpen, setIsExpenseModalOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isCupsModalOpen, setIsCupsModalOpen] = useState(false);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"dashboard" | "fiscal" | "contracts">("dashboard");
  const [isIncomesOpen, setIsIncomesOpen] = useState(false);
  const [isExpensesOpen, setIsExpensesOpen] = useState(false);

  const loadData = async (isInitial = false) => {
    if (!id) return;
    try {
      if (isInitial) setLoading(true);
      const [propData, incData, expData, profData] = await Promise.all([
        getPropertyById(id),
        getIncomes(id),
        getExpenses(id),
        getProfitReport(id),
      ]);
      setProperty(propData);
      setIncomes(incData);
      setExpenses(expData);
      setProfit(profData);
    } catch (error) {
      console.error("Failed to load property data", error);
      toast.error("Error al cargar los datos de la propiedad");
      if (isInitial) navigate("/");
    } finally {
      if (isInitial) setLoading(false);
    }
  };

  useEffect(() => {
    loadData(true);
  }, [id]);

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await uploadPropertyImage(id!, file);
      toast.success("Foto subida correctamente");
      loadData(false);
    } catch (error: any) {
      toast.error(error.message || "Error al subir la foto");
    }
    // Reset the input so the same file can be re-selected
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleCreateIncome = async (data: IncomeCreateInput) => {
    try {
      await createIncome(data);
      setIsIncomeModalOpen(false);
      setIsIncomesOpen(true);
      loadData(false);
      toast.success("Ingreso registrado correctamente");
    } catch (error: any) {
      toast.error(error.message || "Error al registrar el ingreso");
    }
  };

  const handleDeleteIncome = async (incomeId: string) => {
    try {
      await deleteIncome(incomeId);
      toast.success("Ingreso eliminado correctamente");
      loadData(false);
    } catch (error: any) {
      toast.error(error.message || "Error al eliminar el ingreso");
    }
  };

  const handleCreateExpense = async (data: ExpenseCreateInput) => {
    try {
      await createExpense(data);
      setIsExpenseModalOpen(false);
      setIsExpensesOpen(true);
      loadData(false);
      toast.success("Gasto registrado correctamente");
    } catch (error: any) {
      toast.error(error.message || "Error al registrar el gasto");
    }
  };

  const handleDeleteExpense = async (expenseId: string) => {
    try {
      await deleteExpense(expenseId);
      toast.success("Gasto eliminado correctamente");
      loadData(false);
    } catch (error: any) {
      toast.error(error.message || "Error al eliminar el gasto");
    }
  };

  const handleUpdateFiscalData = async (data: FiscalDataInput) => {
    try {
      await updateFiscalData(id!, data);
      toast.success("Datos fiscales actualizados correctamente");
      loadData();
    } catch (error: any) {
      toast.error(error.message || "Error al actualizar los datos fiscales");
    }
  };

  const handleDelete = async () => {
    try {
      await deleteProperty(id!);
      setIsConfirmOpen(false);
      toast.success("Propiedad eliminada correctamente");
      navigate("/");
    } catch (error: any) {
      toast.error(error.message || "Error al eliminar la propiedad");
      setIsConfirmOpen(false);
    }
  };

  if (loading || !property) {
    return (
      <div className="page-container">
        <div className="mb-2"><SkeletonLoader variant="table" count={1} /></div>
        <div className="mb-2"><SkeletonLoader variant="table" count={1} /></div>
        <SkeletonLoader variant="kpi" count={3} />
      </div>
    );
  }

  const totalIncomes = incomes.reduce((acc, curr) => acc + parseFloat(curr.amount), 0);
  const totalExpenses = expenses.reduce((acc, curr) => acc + parseFloat(curr.amount), 0);

  const kpiCards = (
    <>
      <KPICard
        title="Ingresos Totales"
        value={`${totalIncomes.toFixed(2)} €`}
        icon={<TrendingUp size={16} />}
        variant="success"
      />
      <KPICard
        title="Gastos Totales"
        value={`${totalExpenses.toFixed(2)} €`}
        icon={<TrendingDown size={16} />}
        variant="danger"
      />
      <KPICard
        title="Beneficio Neto"
        value={`${parseFloat(profit?.net_profit || "0").toFixed(2)} €`}
        icon={<Scale size={16} />}
        variant="info"
      />
    </>
  );

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <button className="btn btn-link mb-2" onClick={() => navigate("/")} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
            <ArrowLeft size={14} /> Volver al Portafolio
          </button>
          <h1 className="page-title">{property.name}</h1>
          <p className="page-subtitle">
            {property.address.street}, {property.address.city}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-secondary upload-btn" onClick={() => fileInputRef.current?.click()}>
            <Upload size={14} style={{ marginRight: '0.35rem' }} /> Subir Foto
          </button>
          <button className="btn btn-danger" onClick={() => setIsConfirmOpen(true)}>
            <Trash2 size={14} style={{ marginRight: '0.35rem' }} /> Eliminar Propiedad
          </button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png"
          style={{ display: 'none' }}
          onChange={handleImageUpload}
        />
      </div>

      <div className="detail-centered-container">
        {property.image_url ? (
          <div className="detail-hero-layout">
            <div className="detail-hero-image-wrapper">
              <img
                src={`http://localhost:8000${property.image_url}`}
                alt={property.name}
                className="detail-hero-image"
              />
            </div>
            <div className="detail-hero-kpis">
              {kpiCards}
            </div>
          </div>
        ) : (
          <div className="kpi-grid">
            {kpiCards}
          </div>
        )}

        <div className="tabs-container">
          <button 
            className={`tab-btn ${activeTab === "dashboard" ? "active" : ""}`}
            onClick={() => setActiveTab("dashboard")}
          >
            <Wallet size={16} /> Finanzas
          </button>
          <button 
            className={`tab-btn ${activeTab === "contracts" ? "active" : ""}`}
            onClick={() => setActiveTab("contracts")}
          >
            <FileText size={16} /> Contratos
          </button>
          <button 
            className={`tab-btn ${activeTab === "fiscal" ? "active" : ""}`}
            onClick={() => setActiveTab("fiscal")}
          >
            <ReceiptText size={16} /> Datos Fiscales
            <span className={`status-dot ${property.has_fiscal_data ? "complete" : "pending"}`} />
          </button>
        </div>

        {activeTab === "dashboard" ? (
          <div className="finance-sections">
            {/* Collapsible Incomes Section */}
            <div className={`data-section collapsible ${isIncomesOpen ? "open" : "collapsed"}`}>
              <div
                className="collapsible-header"
                onClick={() => setIsIncomesOpen(!isIncomesOpen)}
                role="button"
                tabIndex={0}
                aria-expanded={isIncomesOpen}
              >
                <div className="collapsible-header-left">
                  <span className={`collapsible-chevron ${isIncomesOpen ? "open" : ""}`}>
                    <ChevronRight size={18} />
                  </span>
                  <div className="collapsible-title-group">
                    <h3>Ingresos</h3>
                    <span className="badge badge-neutral">
                      {incomes.length} {incomes.length === 1 ? "registro" : "registros"}
                    </span>
                    <span className="collapsible-total text-success">
                      +{totalIncomes.toFixed(2)} €
                    </span>
                  </div>
                </div>
                <div className="collapsible-header-actions" onClick={(e) => e.stopPropagation()}>
                  <button
                    className="btn btn-sm btn-primary"
                    onClick={() => setIsIncomeModalOpen(true)}
                  >
                    <Plus size={14} style={{ marginRight: '0.3rem' }} />
                    Registrar Ingreso
                  </button>
                </div>
              </div>

              {isIncomesOpen && (
                <div className="collapsible-content">
                  {incomes.length === 0 ? (
                    <p className="empty-text">Aún no hay ingresos registrados.</p>
                  ) : (
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Fecha</th>
                          <th>Categoría</th>
                          <th>Descripción</th>
                          <th className="text-right">Importe</th>
                          <th style={{ width: '40px' }}></th>
                        </tr>
                      </thead>
                      <tbody>
                        {incomes.map((inc) => (
                          <tr key={inc.id}>
                            <td>{inc.date}</td>
                            <td>
                              <span className="badge badge-neutral">
                                {translateIncomeCategory(inc.category)}
                              </span>
                            </td>
                            <td>{inc.description || "—"}</td>
                            <td className="text-right text-success">
                              +{parseFloat(inc.amount).toFixed(2)} €
                            </td>
                            <td className="text-right">
                              <button
                                type="button"
                                onClick={() => handleDeleteIncome(inc.id)}
                                style={{
                                  background: 'none',
                                  border: 'none',
                                  color: '#94a3b8',
                                  cursor: 'pointer',
                                  padding: '4px',
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  borderRadius: '4px',
                                  transition: 'color 0.15s, background-color 0.15s'
                                }}
                                title="Eliminar ingreso"
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.color = '#ef4444';
                                  e.currentTarget.style.backgroundColor = '#fef2f2';
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.color = '#94a3b8';
                                  e.currentTarget.style.backgroundColor = 'transparent';
                                }}
                              >
                                <Trash2 size={16} />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}
            </div>

            {/* Collapsible Expenses Section */}
            <div className={`data-section collapsible ${isExpensesOpen ? "open" : "collapsed"}`}>
              <div
                className="collapsible-header"
                onClick={() => setIsExpensesOpen(!isExpensesOpen)}
                role="button"
                tabIndex={0}
                aria-expanded={isExpensesOpen}
              >
                <div className="collapsible-header-left">
                  <span className={`collapsible-chevron ${isExpensesOpen ? "open" : ""}`}>
                    <ChevronRight size={18} />
                  </span>
                  <div className="collapsible-title-group">
                    <h3>Gastos</h3>
                    <span className="badge badge-neutral">
                      {expenses.length} {expenses.length === 1 ? "registro" : "registros"}
                    </span>
                    <span className="collapsible-total text-danger">
                      -{totalExpenses.toFixed(2)} €
                    </span>
                  </div>
                </div>
                <div className="collapsible-header-actions" onClick={(e) => e.stopPropagation()}>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => setIsCupsModalOpen(true)}
                    title={property.cups_electricity ? `CUPS Luz: ${property.cups_electricity}` : "Configurar código CUPS de luz, gas o agua"}
                  >
                    <SlidersHorizontal size={14} style={{ marginRight: '0.35rem' }} />
                    Configurar CUPS
                  </button>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => setIsUploadModalOpen(true)}
                    title="Importar una o varias facturas de suministros en PDF"
                  >
                    <UploadCloud size={14} style={{ marginRight: '0.3rem' }} />
                    Importar Facturas PDF
                  </button>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => setIsExpenseModalOpen(true)}
                  >
                    <Plus size={14} style={{ marginRight: '0.3rem' }} />
                    Registrar Gasto
                  </button>
                </div>
              </div>

              {isExpensesOpen && (
                <div className="collapsible-content">
                  {expenses.length === 0 ? (
                    <p className="empty-text">Aún no hay gastos registrados.</p>
                  ) : (
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Fecha</th>
                          <th>Categoría</th>
                          <th>Descripción</th>
                          <th className="text-right">Importe</th>
                          <th style={{ width: '40px' }}></th>
                        </tr>
                      </thead>
                      <tbody>
                        {expenses.map((exp) => (
                          <tr key={exp.id}>
                            <td>{exp.date}</td>
                            <td>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                <span className="badge badge-warning">
                                  {translateExpenseCategory(exp.category)}
                                </span>
                                {exp.utility_data && (
                                  <span
                                    className="badge badge-neutral"
                                    style={{
                                      fontSize: '0.75rem',
                                      padding: '0.15rem 0.45rem',
                                      borderRadius: '4px',
                                    }}
                                    title={`CUPS: ${exp.utility_data.cups}${exp.utility_data.invoice_number ? ` | Nº ${exp.utility_data.invoice_number}` : ''}`}
                                  >
                                    {exp.utility_data.provider_name.split(' ')[0]}
                                  </span>
                                )}
                              </div>
                            </td>
                            <td>{exp.description || "—"}</td>
                            <td className="text-right text-danger">
                              -{parseFloat(exp.amount).toFixed(2)} €
                            </td>
                            <td className="text-right">
                              <button
                                type="button"
                                onClick={() => handleDeleteExpense(exp.id)}
                                style={{
                                  background: 'none',
                                  border: 'none',
                                  color: 'var(--text-muted)',
                                  cursor: 'pointer',
                                  padding: '0.25rem',
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  borderRadius: '4px',
                                  transition: 'color 0.15s ease',
                                }}
                                onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--danger)')}
                                onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
                                title="Eliminar gasto"
                              >
                                <Trash2 size={14} />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}
            </div>
          </div>
        ) : activeTab === "contracts" ? (
          <div className="contracts-tab-content">
            <ContractSection propertyId={property.id} />
          </div>
        ) : (
          <div className="fiscal-tab-content">
            <FiscalDataForm 
              propertyId={property.id} 
              onSubmit={handleUpdateFiscalData} 
              onCancel={() => setActiveTab("dashboard")} 
            />
            <FiscalClassificationPanel propertyId={property.id} onClassified={() => loadData(false)} />
            <FiscalReportView propertyId={property.id} />
          </div>
        )}
      </div>

      <Modal
        isOpen={isIncomeModalOpen}
        onClose={() => setIsIncomeModalOpen(false)}
        title="Registrar Ingreso"
      >
        <IncomeForm
          propertyId={property.id}
          onSubmit={handleCreateIncome}
          onCancel={() => setIsIncomeModalOpen(false)}
        />
      </Modal>

      <Modal
        isOpen={isExpenseModalOpen}
        onClose={() => setIsExpenseModalOpen(false)}
        title="Registrar Gasto"
      >
        <ExpenseForm
          propertyId={property.id}
          onSubmit={handleCreateExpense}
          onCancel={() => setIsExpenseModalOpen(false)}
        />
      </Modal>

      <InvoiceUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onSuccess={() => {
          setIsExpensesOpen(true);
          loadData(false);
        }}
      />

      <CupsModal
        isOpen={isCupsModalOpen}
        onClose={() => setIsCupsModalOpen(false)}
        propertyId={property.id}
        initialCups={{
          cups_electricity: property.cups_electricity,
          cups_gas: property.cups_gas,
          cups_water: property.cups_water,
        }}
        onSuccess={() => {
          toast.success("Códigos CUPS actualizados correctamente");
          loadData(false);
        }}
      />

      <ConfirmDialog
        isOpen={isConfirmOpen}
        onConfirm={handleDelete}
        onCancel={() => setIsConfirmOpen(false)}
        title="Eliminar Propiedad"
        message="¿Estás seguro de que quieres eliminar esta propiedad? Esta acción no se puede deshacer."
        confirmLabel="Eliminar"
        variant="danger"
      />
    </div>
  );
}
