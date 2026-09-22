import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
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
  Sparkles,
  Receipt,
  MapPin,
  Building,
  Camera,
  Zap,
} from "lucide-react";
import SuppliesAutomationPanel from "../components/SuppliesAutomationPanel";
import { WelcomeOnboardingBanner } from "../components/WelcomeOnboardingBanner";
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
  BACKEND_STATIC_URL,
} from "../services/api";
import IncomeForm from "../components/IncomeForm";
import ExpenseForm from "../components/ExpenseForm";
import FiscalDataForm from "../components/FiscalDataForm";
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
  const [expensesTab, setExpensesTab] = useState<"list" | "automate">("list");
  const [uploadModalTab, setUploadModalTab] = useState<"upload" | "email">("upload");
  const [searchParams, setSearchParams] = useSearchParams();
  const [showWelcomeBanner, setShowWelcomeBanner] = useState(() => searchParams.get("welcome") === "true");
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadData = async (isInitial = false) => {
    if (!id) return;
    try {
      if (isInitial) setLoading(true);
      setLoadError(null);
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
    } catch (error: any) {
      console.error("Failed to load property data", error);
      setLoadError(error.message || "Error al cargar los datos de la propiedad");
      toast.error("Error al cargar los datos de la propiedad");
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

  if (loadError && !property) {
    return (
      <div className="page-container" style={{ textAlign: "center", padding: "4rem 1rem" }}>
        <h3 style={{ color: "var(--text-primary)", marginBottom: "0.5rem" }}>
          No se pudieron cargar los datos de la propiedad
        </h3>
        <p style={{ color: "var(--text-secondary)", marginBottom: "1.5rem", fontSize: "0.9rem" }}>
          {loadError}
        </p>
        <div style={{ display: "flex", gap: "0.75rem", justifyContent: "center" }}>
          <button className="btn btn-secondary" onClick={() => navigate("/portfolio")}>
            Volver al Portafolio
          </button>
          <button className="btn btn-primary" onClick={() => loadData(true)}>
            Reintentar
          </button>
        </div>
      </div>
    );
  }

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

  const getStatusClass = (status: string) => {
    switch (status.toLowerCase()) {
      case "available": return "badge-success";
      case "rented": return "badge-primary";
      case "maintenance": return "badge-warning";
      default: return "badge-neutral";
    }
  };

  const translateStatus = (status: string) => {
    switch (status.toLowerCase()) {
      case "available": return "Disponible";
      case "rented": return "Alquilado";
      case "maintenance": return "Mantenimiento";
      default: return status;
    }
  };

  const translateType = (type: string) => {
    switch (type.toLowerCase()) {
      case "apartment": return "Piso Residencial";
      case "house": return "Vivienda Unifamiliar";
      case "commercial": return "Local Comercial";
      case "garage": return "Plaza Garaje";
      case "land": return "Suelo / Finca";
      default: return type;
    }
  };

  const getSuppliesStatus = () => {
    const active: string[] = [];
    if (property.cups_electricity) active.push("Luz");
    if (property.cups_gas) active.push("Gas");
    if (property.cups_water) active.push("Agua");

    if (active.length === 0) return { text: "Pendiente vincular", hasSupplies: false };
    if (active.length === 1) {
      const name = active[0];
      const suffix = name === "Gas" ? "vinculado" : "vinculada";
      return { text: `${name} ${suffix}`, hasSupplies: true };
    }
    return { text: `${active.join(" + ")} vinculados`, hasSupplies: true };
  };

  const suppliesStatus = getSuppliesStatus();

  return (
    <div className="page-container">
      {/* Top back navigation */}
      <div className="property-detail-back-bar">
        <button
          className="btn btn-link"
          onClick={() => navigate("/portfolio")}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', padding: 0 }}
        >
          <ArrowLeft size={14} /> Volver a mi Cartera
        </button>
      </div>

      {/* Welcome Onboarding Banner */}
      {showWelcomeBanner && property && (
        <WelcomeOnboardingBanner
          propertyName={property.name}
          onUploadPdf={() => setIsUploadModalOpen(true)}
          onViewFiscal={() => setActiveTab("fiscal")}
          onDismiss={() => {
            setShowWelcomeBanner(false);
            searchParams.delete("welcome");
            setSearchParams(searchParams, { replace: true });
          }}
        />
      )}

      {/* Flush Architectural Dossier Masthead */}
      <div className="property-detail-masthead">
        {/* Left Column: Flush Architectural Photo */}
        <div
          className={`property-detail-masthead__photo ${!property.image_url ? 'property-detail-masthead__photo--empty' : ''}`}
          onClick={() => fileInputRef.current?.click()}
          title={property.image_url ? "Haz clic para cambiar la fotografía" : "Haz clic para subir una fotografía"}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
        >
          {property.image_url ? (
            <>
              <div
                className="property-detail-masthead__photo-bg"
                style={{ backgroundImage: `url(${BACKEND_STATIC_URL}${property.image_url})` }}
              />
              <div className="property-detail-photo-overlay">
                <Camera size={16} />
                <span>Cambiar fotografía</span>
              </div>
            </>
          ) : (
            <div className="property-detail-photo-placeholder">
              <Building size={28} strokeWidth={1.25} />
              <span>Añadir fotografía</span>
            </div>
          )}
        </div>

        {/* Right Column: Identity, Status & Actions */}
        <div className="property-detail-masthead__content">
          <div className="property-detail-masthead__top-row">
            <div className="property-detail-masthead__badges">
              <span className={`badge ${getStatusClass(property.status)}`}>
                {translateStatus(property.status)}
              </span>
              <span className="badge badge-outline">
                {translateType(property.property_type)}
              </span>
              <span className="mono-caption text-muted">
                REF: MAD-{property.id.slice(0, 4).toUpperCase()}
              </span>
            </div>

            <div className="property-detail-masthead__actions">
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload size={13} style={{ marginRight: '0.35rem' }} />
                {property.image_url ? 'Cambiar Foto' : 'Subir Foto'}
              </button>
              <button
                className="btn btn-danger btn-sm"
                onClick={() => setIsConfirmOpen(true)}
              >
                <Trash2 size={13} style={{ marginRight: '0.35rem' }} />
                Eliminar
              </button>
            </div>
          </div>

          <div className="property-detail-masthead__title-group">
            <h1 className="property-detail-masthead__title">{property.name}</h1>
            <p className="property-detail-masthead__address">
              <MapPin size={13} style={{ flexShrink: 0, marginTop: '2px' }} />
              <span>{property.address.street}, {property.address.city} {property.address.postal_code}</span>
            </p>
          </div>

          <div className="property-detail-masthead__footer-row">
            <span className="property-detail-pill">
              <Zap size={12} style={{ color: suppliesStatus.hasSupplies ? 'var(--brand-burgundy)' : 'var(--text-muted)' }} />
              <span>{suppliesStatus.text}</span>
            </span>
            <span className="property-detail-pill">
              <FileText size={12} style={{ color: property.has_fiscal_data ? 'var(--success)' : 'var(--text-muted)' }} />
              <span>{property.has_fiscal_data ? 'Fiscalidad registrada' : 'Pendiente registrar'}</span>
            </span>
          </div>
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
        <div className="kpi-grid">
          {kpiCards}
        </div>

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
                    onClick={() => {
                      setIsExpensesOpen(true);
                      setExpensesTab("automate");
                    }}
                    title="Configurar CUPS y automatizar el registro de facturas por email o PDF"
                    style={{
                      borderColor: expensesTab === "automate" && isExpensesOpen ? "var(--accent-secondary, #2563eb)" : undefined,
                      backgroundColor: expensesTab === "automate" && isExpensesOpen ? "rgba(37, 99, 235, 0.08)" : undefined,
                      color: expensesTab === "automate" && isExpensesOpen ? "var(--accent-secondary, #2563eb)" : undefined,
                    }}
                  >
                    <Sparkles size={14} style={{ marginRight: '0.35rem' }} />
                    Automatizar Suministros
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
                  {/* Expense Subtabs */}
                  <div
                    style={{
                      display: "inline-flex",
                      padding: "3px",
                      backgroundColor: "var(--bg-tertiary)",
                      borderRadius: "var(--radius-md)",
                      marginBottom: "1.25rem",
                      gap: "3px",
                    }}
                  >
                    <button
                      type="button"
                      onClick={() => setExpensesTab("list")}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.45rem",
                        padding: "0.4rem 0.85rem",
                        borderRadius: "var(--radius-sm)",
                        border: "none",
                        fontSize: "0.82rem",
                        fontWeight: expensesTab === "list" ? 600 : 500,
                        backgroundColor: expensesTab === "list" ? "var(--bg-secondary)" : "transparent",
                        color: expensesTab === "list" ? "var(--text-primary)" : "var(--text-secondary)",
                        cursor: "pointer",
                        boxShadow: expensesTab === "list" ? "0 1px 2px rgba(15, 23, 42, 0.08)" : "none",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <Receipt size={14} />
                      <span>Listado de Gastos</span>
                      <span
                        className="badge badge-neutral"
                        style={{
                          fontSize: "0.7rem",
                          padding: "0.1rem 0.4rem",
                          backgroundColor: expensesTab === "list" ? "var(--bg-tertiary)" : "rgba(15, 23, 42, 0.05)",
                        }}
                      >
                        {expenses.length}
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setExpensesTab("automate")}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.45rem",
                        padding: "0.4rem 0.85rem",
                        borderRadius: "var(--radius-sm)",
                        border: "none",
                        fontSize: "0.82rem",
                        fontWeight: expensesTab === "automate" ? 600 : 500,
                        backgroundColor: expensesTab === "automate" ? "var(--bg-secondary)" : "transparent",
                        color: expensesTab === "automate" ? "var(--text-primary)" : "var(--text-secondary)",
                        cursor: "pointer",
                        boxShadow: expensesTab === "automate" ? "0 1px 2px rgba(15, 23, 42, 0.08)" : "none",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <Sparkles size={14} style={{ color: "var(--accent-secondary, #2563eb)" }} />
                      <span>Automatizar Suministros</span>
                      {(property.cups_electricity || property.cups_gas || property.cups_water) && (
                        <span
                          style={{
                            width: "6px",
                            height: "6px",
                            borderRadius: "50%",
                            backgroundColor: "var(--success, #16a34a)",
                          }}
                          title="CUPS configurado"
                        />
                      )}
                    </button>
                  </div>

                  {expensesTab === "list" ? (
                    expenses.length === 0 ? (
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
                                      {exp.utility_data.provider_name ? exp.utility_data.provider_name.split(' ')[0] : 'Suministro'}
                                    </span>
                                  )}
                                </div>
                              </td>
                              <td>{exp.description || "—"}</td>
                              <td className="text-right text-danger">
                                -{parseFloat(String(exp.amount || 0)).toFixed(2)} €
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
                    )
                  ) : (
                    <SuppliesAutomationPanel
                      property={property}
                      onCupsUpdated={() => loadData(false)}
                      onOpenPdfUpload={() => {
                        setUploadModalTab("upload");
                        setIsUploadModalOpen(true);
                      }}
                    />
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
        initialTab={uploadModalTab}
        onSuccess={() => {
          setIsExpensesOpen(true);
          setExpensesTab("list");
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
