import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import type {
  Property,
  Income,
  Expense,
  ProfitReport,
  IncomeCreateInput,
  ExpenseCreateInput,
} from "../types";
import {
  getPropertyById,
  getIncomes,
  getExpenses,
  getProfitReport,
  createIncome,
  createExpense,
  deleteProperty,
  uploadPropertyImage,
} from "../services/api";
import IncomeForm from "../components/IncomeForm";
import ExpenseForm from "../components/ExpenseForm";
import Modal from "../components/Modal";
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
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    if (!id) return;
    try {
      setLoading(true);
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
      navigate("/");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [id]);

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await uploadPropertyImage(id!, file);
      toast.success("Foto subida correctamente");
      loadData();
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
      loadData();
      toast.success("Ingreso registrado correctamente");
    } catch (error: any) {
      toast.error(error.message || "Error al registrar el ingreso");
    }
  };

  const handleCreateExpense = async (data: ExpenseCreateInput) => {
    try {
      await createExpense(data);
      setIsExpenseModalOpen(false);
      loadData();
      toast.success("Gasto registrado correctamente");
    } catch (error: any) {
      toast.error(error.message || "Error al registrar el gasto");
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
        icon="💰"
        variant="success"
      />
      <KPICard
        title="Gastos Totales"
        value={`${totalExpenses.toFixed(2)} €`}
        icon="📉"
        variant="danger"
      />
      <KPICard
        title="Beneficio Neto"
        value={`${parseFloat(profit?.net_profit || "0").toFixed(2)} €`}
        icon="📊"
        variant="info"
      />
    </>
  );

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <button className="btn btn-link mb-2" onClick={() => navigate("/")}>
            ← Volver al Portafolio
          </button>
          <h1 className="page-title">{property.name}</h1>
          <p className="page-subtitle">
            {property.address.street}, {property.address.city}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-secondary upload-btn" onClick={() => fileInputRef.current?.click()}>
            📷 Subir Foto
          </button>
          <button className="btn btn-danger" onClick={() => setIsConfirmOpen(true)}>
            Eliminar Propiedad
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

        <div className="dashboard-grid">
          {/* Incomes Section */}
          <div className="data-section glass-panel">
          <div className="section-header">
            <h3>Ingresos</h3>
            <button
              className="btn btn-sm btn-primary"
              onClick={() => setIsIncomeModalOpen(true)}
            >
              + Registrar Ingreso
            </button>
          </div>
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
                </tr>
              </thead>
              <tbody>
                {incomes.map((inc) => (
                  <tr key={inc.id}>
                    <td>{inc.date}</td>
                    <td><span className="badge badge-neutral">{inc.category}</span></td>
                    <td>{inc.description}</td>
                    <td className="text-right text-success">
                      +{parseFloat(inc.amount).toFixed(2)} €
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Expenses Section */}
        <div className="data-section glass-panel">
          <div className="section-header">
            <h3>Gastos</h3>
            <button
              className="btn btn-sm btn-danger"
              onClick={() => setIsExpenseModalOpen(true)}
            >
              + Registrar Gasto
            </button>
          </div>
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
                </tr>
              </thead>
              <tbody>
                {expenses.map((exp) => (
                  <tr key={exp.id}>
                    <td>{exp.date}</td>
                    <td><span className="badge badge-warning">{exp.category}</span></td>
                    <td>{exp.description}</td>
                    <td className="text-right text-danger">
                      -{parseFloat(exp.amount).toFixed(2)} €
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        </div>
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
