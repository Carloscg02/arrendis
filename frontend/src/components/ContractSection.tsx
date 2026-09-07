import { useState, useEffect } from 'react';
import type { LeaseContract, LeaseContractInput } from '../types';
import { getLeaseContracts, createLeaseContract, updateLeaseContract, deleteLeaseContract } from '../services/api';
import { ContractForm } from './ContractForm';
import { ConfirmDialog } from './ConfirmDialog';
import { useToast } from './Toast';
import { Plus, Edit2, Trash2, FileText } from 'lucide-react';

interface ContractSectionProps {
  propertyId: string;
}

const TYPE_LABELS: Record<string, string> = {
  vivienda_habitual: 'Vivienda Habitual',
  temporal: 'Temporal',
  turistico: 'Turístico',
  comercial: 'Comercial'
};

export function ContractSection({ propertyId }: ContractSectionProps) {
  const toast = useToast();
  const [contracts, setContracts] = useState<LeaseContract[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingContract, setEditingContract] = useState<LeaseContract | undefined>();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadContracts = async (isInitial = false) => {
    try {
      if (isInitial) setLoading(true);
      const data = await getLeaseContracts(propertyId);
      setContracts(data);
    } catch (err: any) {
      setError(err.message || 'Error al cargar contratos');
    } finally {
      if (isInitial) setLoading(false);
    }
  };

  useEffect(() => {
    loadContracts(true);
  }, [propertyId]);

  const handleSave = async (data: LeaseContractInput) => {
    try {
      if (editingContract) {
        await updateLeaseContract(editingContract.id, data);
        toast.success("Contrato actualizado correctamente");
      } else {
        await createLeaseContract(propertyId, data);
        toast.success("Contrato registrado correctamente");
      }
      setIsFormOpen(false);
      setEditingContract(undefined);
      loadContracts(false);
    } catch (err: any) {
      toast.error(err.message || 'Error al guardar contrato');
    }
  };

  const handleConfirmDelete = async () => {
    if (!deletingId) return;
    try {
      await deleteLeaseContract(deletingId);
      toast.success("Contrato eliminado correctamente");
      setDeletingId(null);
      loadContracts(false);
    } catch (err: any) {
      toast.error(err.message || 'Error al eliminar');
      setDeletingId(null);
    }
  };

  if (loading) return <div className="loading">Cargando contratos...</div>;
  if (error) return <div className="error-message">{error}</div>;

  return (
    <div className="contracts-section">
      <div className="section-header">
        <h3>Contratos de Arrendamiento</h3>
        <button className="btn btn-sm btn-primary" onClick={() => { setEditingContract(undefined); setIsFormOpen(true); }}>
          <Plus size={14} style={{ marginRight: '0.3rem' }} /> Nuevo Contrato
        </button>
      </div>

      {contracts.length === 0 ? (
        <div className="empty-state">
          <FileText size={36} className="empty-icon" strokeWidth={1.5} />
          <p className="empty-text">No hay contratos registrados para esta propiedad.</p>
        </div>
      ) : (
        <div className="contracts-list">
          {contracts.map(contract => (
            <div key={contract.id} className="contract-card">
              <div className="contract-header">
                <h4>{contract.tenant_name}</h4>
                <div className="contract-badges">
                  <span className={`status-badge ${contract.is_active ? 'active' : 'inactive'}`}>
                    {contract.is_active ? 'Activo' : 'Finalizado'}
                  </span>
                  <span className={`type-badge ${contract.lease_type}`}>
                    {TYPE_LABELS[contract.lease_type] || contract.lease_type}
                  </span>
                </div>
              </div>
              <div className="contract-details">
                <p><strong>NIF:</strong> {contract.tenant_nif}</p>
                <p><strong>Renta:</strong> {contract.monthly_rent} €/mes</p>
                <p><strong>Inicio:</strong> {contract.start_date}</p>
                <p><strong>Fin:</strong> {contract.end_date || 'Indefinido'}</p>
              </div>
              <div className="contract-actions">
                <button className="icon-btn" onClick={() => { setEditingContract(contract); setIsFormOpen(true); }} title="Editar">
                  <Edit2 size={16} />
                </button>
                <button className="icon-btn delete" onClick={() => setDeletingId(contract.id)} title="Eliminar">
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {isFormOpen && (
        <ContractForm
          contract={editingContract}
          onSave={handleSave}
          onClose={() => { setIsFormOpen(false); setEditingContract(undefined); }}
        />
      )}

      <ConfirmDialog
        isOpen={Boolean(deletingId)}
        title="Eliminar Contrato"
        message="¿Estás seguro de que deseas eliminar este contrato de arrendamiento? Esta acción no se puede deshacer."
        confirmLabel="Eliminar"
        variant="danger"
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeletingId(null)}
      />
    </div>
  );
}
