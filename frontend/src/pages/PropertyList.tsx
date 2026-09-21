import { useEffect, useState } from "react";
import { Plus, Building2 } from "lucide-react";
import type { Property, PropertyCreateInput } from "../types";
import { getProperties, createProperty } from "../services/api";
import PropertyCard from "../components/PropertyCard";
import PropertyForm from "../components/PropertyForm";
import Modal from "../components/Modal";
import { useToast } from "../components/Toast";
import { SkeletonLoader } from "../components/SkeletonLoader";

export default function PropertyList() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  const loadProperties = async () => {
    try {
      setLoading(true);
      const data = await getProperties();
      setProperties(data);
    } catch (error) {
      console.error("Failed to load properties", error);
      toast.error("Error al cargar las propiedades");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProperties();
  }, []);

  const handleCreateProperty = async (data: PropertyCreateInput) => {
    try {
      await createProperty(data);
      setIsModalOpen(false);
      loadProperties();
      toast.success("Propiedad creada correctamente");
    } catch (error: any) {
      toast.error(error.message || "Error al crear la propiedad");
    }
  };

  const rentedCount = properties.filter(
    (p) => p.status && p.status.toLowerCase() === "rented"
  ).length;

  const fiscalCount = properties.filter((p) => Boolean(p.has_fiscal_data)).length;

  return (
    <div className="page-container">
      {/* Portfolio Architectural Masthead */}
      <header className="portfolio-masthead">
        <div className="portfolio-masthead__top">
          <div>
            <span className="mono-eyebrow" style={{ marginBottom: "0.45rem" }}>
              CUADERNO PATRIMONIAL DE ACTIVOS
            </span>
            <h1 className="page-title">Cartera de Inmuebles</h1>
          </div>

          <button
            className="btn btn-primary"
            onClick={() => setIsModalOpen(true)}
          >
            <Plus size={15} style={{ marginRight: "0.4rem" }} />
            <span>Incorporar Inmueble</span>
          </button>
        </div>

        {!loading && properties.length > 0 && (
          <div className="portfolio-masthead__meta">
            <div className="portfolio-meta-item">
              <span>Activos en Registro:</span>
              <strong>
                {properties.length}{" "}
                {properties.length === 1 ? "Inmueble" : "Inmuebles"}
              </strong>
            </div>
            <div className="portfolio-meta-item">
              <span>Ocupación LAU:</span>
              <strong className="text-garnet">
                {rentedCount} en alquiler (
                {Math.round((rentedCount / properties.length) * 100)}%)
              </strong>
            </div>
            <div className="portfolio-meta-item">
              <span>Ficha Fiscal Modelo 100:</span>
              <strong>
                {fiscalCount} de {properties.length} vinculados
              </strong>
            </div>
          </div>
        )}
      </header>

      {loading ? (
        <SkeletonLoader variant="card" count={3} />
      ) : properties.length === 0 ? (
        <div className="empty-state">
          <Building2 size={38} strokeWidth={1.25} className="empty-icon" />
          <h3>No hay inmuebles en su cartera</h3>
          <p>Comience incorporando la primera vivienda para gestionar contratos y suministros.</p>
          <button
            className="btn btn-primary mt-4"
            onClick={() => setIsModalOpen(true)}
          >
            <Plus size={15} style={{ marginRight: "0.4rem" }} />
            <span>Añadir Primer Inmueble</span>
          </button>
        </div>
      ) : (
        <div className="property-grid">
          {properties.map((property) => (
            <PropertyCard key={property.id} property={property} />
          ))}

          {/* Architectural Slot: Add Next Property */}
          <div
            className="property-slot-add"
            onClick={() => setIsModalOpen(true)}
            tabIndex={0}
            role="button"
            onKeyDown={(e) => e.key === "Enter" && setIsModalOpen(true)}
          >
            <div className="property-slot-add__icon">
              <Plus size={20} />
            </div>
            <div>
              <h3 className="property-slot-add__title">
                Incorporar un nuevo inmueble a la cartera
              </h3>
              <p className="property-slot-add__text">
                Añada una nueva referencia catastral para vincular facturas de suministros por CUPS y deducir la amortización del 3% en el IRPF.
              </p>
            </div>
          </div>
        </div>
      )}

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Añadir Nueva Propiedad a la Cartera"
      >
        <PropertyForm
          onSubmit={handleCreateProperty}
          onCancel={() => setIsModalOpen(false)}
        />
      </Modal>
    </div>
  );
}
