import React, { useState, useEffect } from 'react';
import type { LeaseContract, LeaseContractInput } from '../types';
import { X } from 'lucide-react';

interface ContractFormProps {
  contract?: LeaseContract;
  onSave: (data: LeaseContractInput) => void;
  onClose: () => void;
}

export function ContractForm({ contract, onSave, onClose }: ContractFormProps) {
  const [formData, setFormData] = useState<LeaseContractInput>({
    tenant_name: '',
    tenant_nif: '',
    start_date: '',
    end_date: '',
    monthly_rent: 0,
    lease_type: 'vivienda_habitual',
  });
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  useEffect(() => {
    if (contract) {
      setFormData({
        tenant_name: contract.tenant_name,
        tenant_nif: contract.tenant_nif,
        start_date: contract.start_date,
        end_date: contract.end_date || '',
        monthly_rent: parseFloat(contract.monthly_rent),
        lease_type: contract.lease_type,
      });
    }
  }, [contract]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'monthly_rent' ? parseFloat(value) || 0 : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.tenant_name.trim()) return setError('El nombre del inquilino es obligatorio.');
    if (!formData.tenant_nif.trim()) return setError('El NIF del inquilino es obligatorio.');
    if (!formData.start_date) return setError('La fecha de inicio es obligatoria.');
    if (formData.monthly_rent <= 0) return setError('La renta mensual debe ser mayor que 0.');

    try {
      setIsSubmitting(true);
      await Promise.resolve(onSave({
        ...formData,
        end_date: formData.end_date || null
      }));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>{contract ? 'Editar Contrato' : 'Nuevo Contrato'}</h2>
          <button onClick={onClose} className="icon-btn" aria-label="Cerrar modal"><X size={20} /></button>
        </div>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit} className="form-layout">
          <div className="form-group">
            <label htmlFor="tenant_name">Nombre Inquilino *</label>
            <input id="tenant_name" type="text" name="tenant_name" value={formData.tenant_name} onChange={handleChange} required />
          </div>
          
          <div className="form-group">
            <label htmlFor="tenant_nif">NIF Inquilino *</label>
            <input id="tenant_nif" type="text" name="tenant_nif" value={formData.tenant_nif} onChange={handleChange} required />
          </div>
          
          <div className="form-group">
            <label htmlFor="start_date">Fecha Inicio *</label>
            <input id="start_date" type="date" name="start_date" value={formData.start_date} onChange={handleChange} required />
          </div>
          
          <div className="form-group">
            <label htmlFor="end_date">Fecha Fin</label>
            <input id="end_date" type="date" name="end_date" value={formData.end_date || ''} onChange={handleChange} />
          </div>
          
          <div className="form-group">
            <label htmlFor="monthly_rent">Renta Mensual (€) *</label>
            <input id="monthly_rent" type="number" step="0.01" min="0.01" name="monthly_rent" value={formData.monthly_rent || ''} onChange={handleChange} required />
          </div>
          
          <div className="form-group">
            <label htmlFor="lease_type">Tipo de Contrato *</label>
            <select id="lease_type" name="lease_type" value={formData.lease_type} onChange={handleChange} required>
              <option value="vivienda_habitual">Vivienda Habitual</option>
              <option value="temporal">Temporal</option>
              <option value="turistico">Turístico</option>
              <option value="comercial">Comercial</option>
            </select>
          </div>
          
          <div className="form-actions">
            <button type="button" onClick={onClose} className="btn-secondary" disabled={isSubmitting}>Cancelar</button>
            <button type="submit" className="btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Guardando...' : 'Guardar Contrato'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
