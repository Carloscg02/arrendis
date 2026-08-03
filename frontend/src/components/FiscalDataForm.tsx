import { useState, useEffect } from "react";
import type { FiscalDataInput } from "../types";
import { getFiscalData } from "../services/api";
import { Building, Map } from "lucide-react";

interface FiscalDataFormProps {
  propertyId: string;
  onSubmit: (data: FiscalDataInput) => void;
  onCancel: () => void;
}

export default function FiscalDataForm({ propertyId, onSubmit, onCancel }: FiscalDataFormProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cadastralRef, setCadastralRef] = useState("");
  const [landValue, setLandValue] = useState("");
  const [constructionValue, setConstructionValue] = useState("");
  
  const [purchasePrice, setPurchasePrice] = useState("");
  const [constructionPortion, setConstructionPortion] = useState("");
  const [landPortion, setLandPortion] = useState("");
  const [transferTax, setTransferTax] = useState("");
  const [notaryFees, setNotaryFees] = useState("");
  const [registryFees, setRegistryFees] = useState("");
  const [acquisitionDate, setAcquisitionDate] = useState("");

  const [expandedSection, setExpandedSection] = useState<"cadastral" | "acquisition" | "both">("both");

  useEffect(() => {
    async function load() {
      try {
        const data = await getFiscalData(propertyId);
        if (data) {
          setCadastralRef(data.cadastral_ref || "");
          if (data.cadastral_breakdown) {
            setLandValue(data.cadastral_breakdown.land_value);
            setConstructionValue(data.cadastral_breakdown.construction_value);
          }
          if (data.acquisition_cost) {
            setPurchasePrice(data.acquisition_cost.purchase_price);
            setConstructionPortion(data.acquisition_cost.construction_portion);
            setLandPortion(data.acquisition_cost.land_portion);
            setTransferTax(data.acquisition_cost.transfer_tax);
            setNotaryFees(data.acquisition_cost.notary_fees);
            setRegistryFees(data.acquisition_cost.registry_fees);
          }
          if (data.acquisition_date) {
            setAcquisitionDate(data.acquisition_date);
          }
        }
      } catch (err) {
        console.error("No fiscal data found or error loading it", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [propertyId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const refClean = cadastralRef.trim();
    if (refClean.length > 0 && refClean.length !== 20) {
      setError(`La referencia catastral debe tener exactamente 20 caracteres (actualmente tiene ${refClean.length}).`);
      return;
    }

    const input: FiscalDataInput = {};
    
    if (refClean) input.cadastral_ref = refClean;

    if (landValue || constructionValue) {
      input.cadastral_breakdown = {
        land_value: parseFloat(landValue) || 0,
        construction_value: parseFloat(constructionValue) || 0,
      };
    }

    if (purchasePrice || constructionPortion || landPortion || transferTax || notaryFees || registryFees) {
      input.acquisition_cost = {
        purchase_price: parseFloat(purchasePrice) || 0,
        construction_portion: parseFloat(constructionPortion) || 0,
        land_portion: parseFloat(landPortion) || 0,
        transfer_tax: parseFloat(transferTax) || 0,
        notary_fees: parseFloat(notaryFees) || 0,
        registry_fees: parseFloat(registryFees) || 0,
      };
    }

    if (acquisitionDate) input.acquisition_date = acquisitionDate;

    onSubmit(input);
  };

  if (loading) {
    return <div className="p-4 text-center">Cargando datos fiscales...</div>;
  }

  const toggleSection = (section: "cadastral" | "acquisition") => {
    if (expandedSection === "both") {
      setExpandedSection(section === "cadastral" ? "acquisition" : "cadastral");
    } else if (expandedSection === section) {
      setExpandedSection("both");
    } else {
      setExpandedSection("both");
    }
  };

  return (
    <form className="form fiscal-form" onSubmit={handleSubmit}>
      {error && (
        <div className="report-warning" style={{ marginBottom: "1rem" }}>
          ⚠️ {error}
        </div>
      )}
      <div className={`fiscal-section ${expandedSection === "both" || expandedSection === "cadastral" ? "expanded" : "collapsed"}`}>
        <div className="fiscal-section-header" onClick={() => toggleSection("cadastral")}>
          <div className="fiscal-section-title">
            <Map className="fiscal-icon" size={20} />
            <h4>Datos Catastrales</h4>
          </div>
          <button type="button" className="btn btn-sm btn-secondary">
            {expandedSection === "both" || expandedSection === "cadastral" ? "Colapsar" : "Expandir"}
          </button>
        </div>
        
        <div className="fiscal-section-content">
          <div className="form-group">
            <label>Referencia Catastral (20 caracteres)</label>
            <input
              type="text"
              value={cadastralRef}
              onChange={(e) => setCadastralRef(e.target.value)}
              placeholder="Ej: 1234567AB1234C0001XY"
              maxLength={20}
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Valor Suelo (€)</label>
              <input
                type="number"
                step="0.01"
                value={landValue}
                onChange={(e) => setLandValue(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Valor Construcción (€)</label>
              <input
                type="number"
                step="0.01"
                value={constructionValue}
                onChange={(e) => setConstructionValue(e.target.value)}
              />
            </div>
          </div>
        </div>
      </div>

      <div className={`fiscal-section ${expandedSection === "both" || expandedSection === "acquisition" ? "expanded" : "collapsed"}`}>
        <div className="fiscal-section-header" onClick={() => toggleSection("acquisition")}>
          <div className="fiscal-section-title">
            <Building className="fiscal-icon" size={20} />
            <h4>Datos de Adquisición</h4>
          </div>
          <button type="button" className="btn btn-sm btn-secondary">
            {expandedSection === "both" || expandedSection === "acquisition" ? "Colapsar" : "Expandir"}
          </button>
        </div>
        
        <div className="fiscal-section-content">
          <div className="form-row">
            <div className="form-group">
              <label>Fecha de Compra</label>
              <input
                type="date"
                value={acquisitionDate}
                onChange={(e) => setAcquisitionDate(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Precio Compra (€)</label>
              <input
                type="number"
                step="0.01"
                value={purchasePrice}
                onChange={(e) => setPurchasePrice(e.target.value)}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Porción Suelo (€)</label>
              <input
                type="number"
                step="0.01"
                value={landPortion}
                onChange={(e) => setLandPortion(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Porción Construcción (€)</label>
              <input
                type="number"
                step="0.01"
                value={constructionPortion}
                onChange={(e) => setConstructionPortion(e.target.value)}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>ITP (€)</label>
              <input
                type="number"
                step="0.01"
                value={transferTax}
                onChange={(e) => setTransferTax(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Notaría (€)</label>
              <input
                type="number"
                step="0.01"
                value={notaryFees}
                onChange={(e) => setNotaryFees(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Registro (€)</label>
              <input
                type="number"
                step="0.01"
                value={registryFees}
                onChange={(e) => setRegistryFees(e.target.value)}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel}>
          Cancelar
        </button>
        <button type="submit" className="btn btn-primary">
          Guardar Datos Fiscales
        </button>
      </div>
    </form>
  );
}
