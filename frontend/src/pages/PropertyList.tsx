import { useEffect, useState } from "react";
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

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Portafolio de Inmuebles</h1>
          <p className="page-subtitle">Gestiona tus propiedades de alquiler</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setIsModalOpen(true)}
        >
          + Nueva Propiedad
        </button>
      </div>

      {loading ? (
        <SkeletonLoader variant="card" count={6} />
      ) : properties.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🏢</div>
          <h3>No se encontraron propiedades</h3>
          <p>Comienza añadiendo tu primera propiedad de alquiler.</p>
          <button
            className="btn btn-primary mt-4"
            onClick={() => setIsModalOpen(true)}
          >
            Añadir Propiedad
          </button>
        </div>
      ) : (
        <div className="property-grid">
          {properties.map((property) => (
            <PropertyCard key={property.id} property={property} />
          ))}
        </div>
      )}

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Añadir Nueva Propiedad"
      >
        <PropertyForm
          onSubmit={handleCreateProperty}
          onCancel={() => setIsModalOpen(false)}
        />
      </Modal>
    </div>
  );
}
