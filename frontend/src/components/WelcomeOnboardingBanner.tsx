import React from 'react';
import { Sparkles, UploadCloud, FileText, X } from 'lucide-react';

interface WelcomeOnboardingBannerProps {
  propertyName: string;
  onUploadPdf: () => void;
  onViewFiscal: () => void;
  onDismiss: () => void;
}

export const WelcomeOnboardingBanner: React.FC<WelcomeOnboardingBannerProps> = ({
  propertyName,
  onUploadPdf,
  onViewFiscal,
  onDismiss,
}) => {
  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        border: '1px solid var(--panel-border, #e5e2dd)',
        borderLeft: '4px solid var(--brand-burgundy, #6b0008)',
        borderRadius: '8px',
        padding: '1.25rem 1.5rem',
        marginBottom: '1.5rem',
        boxShadow: 'var(--shadow-card, 0 1px 3px rgba(0,0,0,0.05))',
        position: 'relative',
      }}
    >
      {/* Botón cerrar */}
      <button
        onClick={onDismiss}
        style={{
          position: 'absolute',
          top: '1rem',
          right: '1rem',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: 'var(--text-muted, #94a3b8)',
          padding: '0.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '4px',
        }}
        title="Cerrar guía"
      >
        <X size={16} />
      </button>

      {/* Cabecera */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.35rem' }}>
        <Sparkles size={18} color="var(--brand-burgundy, #6b0008)" />
        <h3
          style={{
            margin: 0,
            fontSize: '1.05rem',
            fontFamily: 'var(--font-serif)',
            fontWeight: 500,
            color: 'var(--text-primary, #0f172a)',
            letterSpacing: '-0.01em',
          }}
        >
          ¡Enhorabuena! Has registrado «{propertyName}» con éxito
        </h3>
      </div>

      <p
        style={{
          margin: '0 0 1rem 0',
          fontSize: '0.85rem',
          color: 'var(--text-secondary, #475569)',
          lineHeight: 1.45,
          maxWidth: '90%',
        }}
      >
        Tu patrimonio ya está en Arrendis. Para experimentar la automatización y el cálculo tributario oficial, te recomendamos probar estas dos acciones:
      </p>

      {/* Grid de 2 acciones inmediatas */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '1rem',
        }}
      >
        {/* Acción 1: Subir factura */}
        <div
          style={{
            backgroundColor: 'var(--bg-primary, #f9f7f5)',
            border: '1px solid var(--panel-border, #e5e2dd)',
            borderRadius: '6px',
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            gap: '0.75rem',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.3rem' }}>
              <UploadCloud size={16} color="var(--brand-burgundy, #6b0008)" />
              <strong style={{ fontSize: '0.88rem', color: 'var(--text-primary)' }}>
                1. Prueba la lectura de facturas
              </strong>
            </div>
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              Arrastra un PDF de luz o gas (Endesa, Iberdrola, Repsol...) para ver cómo la IA extrae importes y fechas al instante.
            </p>
          </div>
          <button
            onClick={onUploadPdf}
            className="btn btn-secondary btn-sm"
            style={{
              alignSelf: 'flex-start',
              fontSize: '0.8rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
            }}
          >
            <UploadCloud size={14} /> Subir Factura PDF
          </button>
        </div>

        {/* Acción 2: Ver borrador fiscal */}
        <div
          style={{
            backgroundColor: 'var(--bg-primary, #f9f7f5)',
            border: '1px solid var(--panel-border, #e5e2dd)',
            borderRadius: '6px',
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            gap: '0.75rem',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.3rem' }}>
              <FileText size={16} color="var(--brand-burgundy, #6b0008)" />
              <strong style={{ fontSize: '0.88rem', color: 'var(--text-primary)' }}>
                2. Consulta tu Borrador Fiscal AEAT
              </strong>
            </div>
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              Comprueba el cálculo del 3% de amortización y cómo se estructuran las casillas oficiales del Modelo 100 de la Renta.
            </p>
          </div>
          <button
            onClick={onViewFiscal}
            className="btn btn-secondary btn-sm"
            style={{
              alignSelf: 'flex-start',
              fontSize: '0.8rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
            }}
          >
            <FileText size={14} /> Ver Borrador IRPF
          </button>
        </div>
      </div>
    </div>
  );
};
