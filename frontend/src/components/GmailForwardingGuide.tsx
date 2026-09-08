import { useState } from "react";
import { 
  Check, 
  Copy, 
  ChevronDown, 
  ChevronUp, 
  ShieldCheck, 
  Maximize2,
  X
} from "lucide-react";

interface GmailForwardingGuideProps {
  inboundAddress: string;
}

interface StepItem {
  id: number;
  title: string;
  subtitle: string;
  instructions: string[];
  images: {
    src: string;
    alt: string;
    caption: string;
  }[];
  tip?: string;
  copyValue?: string;
  copyLabel?: string;
}

export default function GmailForwardingGuide({ inboundAddress }: GmailForwardingGuideProps) {
  const [openSteps, setOpenSteps] = useState<Record<number, boolean>>({
    1: true,
    2: false,
    3: false,
  });
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [previewImage, setPreviewImage] = useState<{ src: string; alt: string; caption: string } | null>(null);

  const toggleStep = (stepId: number) => {
    setOpenSteps((prev) => ({
      ...prev,
      [stepId]: !prev[stepId],
    }));
  };

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const steps: StepItem[] = [
    {
      id: 1,
      title: "Autorizar la dirección en Gmail",
      subtitle: "Solo se hace una vez y nuestro sistema lo auto-confirma en 2 segundos.",
      instructions: [
        "Abre Gmail en el navegador de tu ordenador.",
        "Haz clic en el icono de la rueda de ajustes (arriba a la derecha) y pulsa en 'Ver todos los ajustes'.",
        "Selecciona la pestaña 'Reenvío y correo POP/IMAP'.",
        "Pulsa el botón 'Añadir una dirección de reenvío', introduce la dirección de Arrendis y pulsa 'Siguiente'.",
      ],
      copyValue: inboundAddress,
      copyLabel: "Copiar dirección",
      images: [
        {
          src: "/guides/gmail/paso1_ajustes.png",
          alt: "Paso 1: Ajustes de Gmail y Ver todos los ajustes",
          caption: "1. Icono de ajustes  ➔  2. 'Ver todos los ajustes'",
        },
        {
          src: "/guides/gmail/paso2_direccion_reenvio.png",
          alt: "Paso 2: Añadir dirección de reenvío",
          caption: "Pestaña 'Reenvío y correo POP/IMAP' ➔ Introducir dirección",
        },
      ],
      tip: "Verificación instantánea: Al pulsar 'Siguiente', nuestro sistema valida automáticamente el permiso con Google en menos de 2 segundos. No necesitas esperar ningún código por correo.",
    },
    {
      id: 2,
      title: "Crear el filtro de búsqueda para tu compañía",
      subtitle: "Define qué correos contienen tus facturas para que se reenvíen solos.",
      instructions: [
        "En la barra superior de búsqueda de Gmail, haz clic en el icono de filtros de búsqueda (a la derecha del buscador).",
        "En el campo 'De:', escribe el remitente o nombre de tu compañía suministradora (ej: clientes@tuiberdrola.es o tu compañía de luz/gas/agua).",
        "Marca la casilla 'Contiene archivos adjuntos'.",
        "Haz clic en el botón 'Crear filtro' abajo a la derecha.",
      ],
      copyValue: "clientes@tuiberdrola.es",
      copyLabel: "Copiar ejemplo Iberdrola",
      images: [
        {
          src: "/guides/gmail/paso3.1_criterios_filtro.png",
          alt: "Paso 2.1: Icono de filtros de búsqueda",
          caption: "Pulsar el icono de filtros a la derecha del buscador",
        },
        {
          src: "/guides/gmail/paso3.2_criterios_filtro.png",
          alt: "Paso 2.2: Criterios del filtro",
          caption: "Rellenar remitente ('De:') + Marcar 'Contiene archivos adjuntos' ➔ 'Crear filtro'",
        },
      ],
    },
    {
      id: 3,
      title: "Activar el reenvío automático",
      subtitle: "Conecta el filtro con tu buzón de Arrendis.",
      instructions: [
        "En la siguiente pantalla de opciones, marca la casilla 'Reenviarlo a:'.",
        "En el desplegable, selecciona la dirección de Arrendis que autorizaste en el Paso 1.",
        "Haz clic en el botón azul 'Crear filtro' para confirmar.",
      ],
      images: [
        {
          src: "/guides/gmail/paso4_aplicar_reenvio.png",
          alt: "Paso 3: Marcar Reenviarlo a y Crear filtro",
          caption: "Marcar 'Reenviarlo a: facturas@arrendis.com' ➔ Pulsar 'Crear filtro'",
        },
      ],
      tip: "Regla completada: A partir de ahora, cada factura que tu compañía te mande por correo entrará automáticamente en tu panel de Arrendis con sus importes y fechas contabilizados.",
    },
  ];

  return (
    <div className="gmail-guide-container" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      {/* Privacy & Safety Confidence Banner */}
      <div
        style={{
          padding: "0.85rem 1rem",
          backgroundColor: "rgba(37, 99, 235, 0.05)",
          border: "1px solid rgba(37, 99, 235, 0.2)",
          borderRadius: "var(--radius-md)",
          display: "flex",
          gap: "0.75rem",
          alignItems: "flex-start",
        }}
      >
        <ShieldCheck size={18} style={{ color: "var(--accent-secondary, #2563eb)", flexShrink: 0, marginTop: "0.15rem" }} />
        <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
          <strong style={{ color: "var(--text-primary)", display: "block", marginBottom: "0.25rem" }}>
            100% Seguro y Privado
          </strong>
          Esta configuración se realiza una única vez por usuario (no por cada propiedad) y una única vez por compañía suministradora. A partir de ese momento, todas tus propiedades que tengan su código CUPS configurado registrarán y contabilizarán los gastos automáticamente. Arrendis nunca accede a tu cuenta de Google, no lee tus correos personales ni solicita contraseñas.
        </div>
      </div>

      {/* Accordion Steps */}
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {steps.map((step) => {
          const isOpen = !!openSteps[step.id];

          return (
            <div
              key={step.id}
              style={{
                border: "1px solid var(--panel-border)",
                borderRadius: "var(--radius-lg)",
                backgroundColor: "var(--bg-secondary)",
                overflow: "hidden",
                transition: "all 0.2s ease",
              }}
            >
              {/* Step Header Accordion Toggle */}
              <button
                type="button"
                onClick={() => toggleStep(step.id)}
                style={{
                  width: "100%",
                  padding: "0.85rem 1.15rem",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  background: isOpen ? "var(--bg-tertiary)" : "transparent",
                  border: "none",
                  borderBottom: isOpen ? "1px solid var(--panel-border)" : "none",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "background 0.15s ease",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <span
                    style={{
                      width: "24px",
                      height: "24px",
                      borderRadius: "50%",
                      backgroundColor: isOpen ? "var(--accent-secondary, #2563eb)" : "var(--panel-border)",
                      color: isOpen ? "#ffffff" : "var(--text-secondary)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "0.8rem",
                      fontWeight: 700,
                      flexShrink: 0,
                    }}
                  >
                    {step.id}
                  </span>
                  <div>
                    <span style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-primary)", display: "block" }}>
                      {step.title}
                    </span>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      {step.subtitle}
                    </span>
                  </div>
                </div>

                <div style={{ color: "var(--text-muted)", display: "flex", alignItems: "center" }}>
                  {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </div>
              </button>

              {/* Step Content */}
              {isOpen && (
                <div style={{ padding: "1.15rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
                  {/* Instructions List */}
                  <ol style={{ margin: 0, paddingLeft: "1.25rem", display: "flex", flexDirection: "column", gap: "0.45rem" }}>
                    {step.instructions.map((inst, i) => (
                      <li key={i} style={{ fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
                        {inst}
                      </li>
                    ))}
                  </ol>

                  {/* Copy Helper (if available) */}
                  {step.copyValue && (
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        padding: "0.5rem 0.75rem",
                        backgroundColor: "var(--bg-primary)",
                        border: "1px solid var(--panel-border)",
                        borderRadius: "var(--radius-md)",
                        gap: "0.5rem",
                      }}
                    >
                      <code style={{ fontSize: "0.85rem", fontFamily: "monospace", color: "var(--text-primary)", wordBreak: "break-all" }}>
                        {step.copyValue}
                      </code>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={() => handleCopy(step.copyValue!, `step-${step.id}`)}
                        style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem", display: "inline-flex", alignItems: "center", gap: "0.3rem", flexShrink: 0 }}
                      >
                        {copiedKey === `step-${step.id}` ? <Check size={13} style={{ color: "var(--success)" }} /> : <Copy size={13} />}
                        {copiedKey === `step-${step.id}` ? "Copiado" : step.copyLabel || "Copiar"}
                      </button>
                    </div>
                  )}

                  {/* Screenshots Grid */}
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: step.images.length > 1 ? "repeat(auto-fit, minmax(240px, 1fr))" : "1fr",
                      gap: "0.85rem",
                      marginTop: "0.25rem",
                    }}
                  >
                    {step.images.map((img, idx) => (
                      <div
                        key={idx}
                        style={{
                          border: "1px solid var(--panel-border)",
                          borderRadius: "var(--radius-md)",
                          backgroundColor: "var(--bg-primary)",
                          overflow: "hidden",
                          display: "flex",
                          flexDirection: "column",
                        }}
                      >
                        <div
                          style={{
                            position: "relative",
                            cursor: "zoom-in",
                            overflow: "hidden",
                            backgroundColor: "#1e1e1e",
                          }}
                          onClick={() => setPreviewImage(img)}
                          title="Haz clic para ampliar la imagen"
                        >
                          <img
                            src={img.src}
                            alt={img.alt}
                            loading="lazy"
                            style={{
                              width: "100%",
                              height: "auto",
                              maxHeight: "220px",
                              objectFit: "contain",
                              display: "block",
                              transition: "transform 0.2s ease",
                            }}
                          />
                          <div
                            style={{
                              position: "absolute",
                              right: "8px",
                              bottom: "8px",
                              backgroundColor: "rgba(0, 0, 0, 0.65)",
                              color: "#fff",
                              padding: "0.2rem 0.45rem",
                              borderRadius: "var(--radius-sm)",
                              fontSize: "0.7rem",
                              display: "flex",
                              alignItems: "center",
                              gap: "0.25rem",
                            }}
                          >
                            <Maximize2 size={11} /> Ampliar
                          </div>
                        </div>
                        <div
                          style={{
                            padding: "0.5rem 0.75rem",
                            fontSize: "0.75rem",
                            color: "var(--text-muted)",
                            borderTop: "1px solid var(--panel-border)",
                            backgroundColor: "var(--bg-secondary)",
                            fontWeight: 500,
                          }}
                        >
                          {img.caption}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Tip Callout */}
                  {step.tip && (
                    <div
                      style={{
                        padding: "0.6rem 0.85rem",
                        backgroundColor: "var(--bg-tertiary)",
                        borderLeft: "3px solid var(--accent-secondary, #2563eb)",
                        borderRadius: "0 var(--radius-sm) var(--radius-sm) 0",
                        fontSize: "0.78rem",
                        color: "var(--text-secondary)",
                        lineHeight: 1.45,
                      }}
                    >
                      {step.tip}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Fullscreen Image Preview Lightbox */}
      {previewImage && (
        <div
          onClick={() => setPreviewImage(null)}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.85)",
            zIndex: 9999,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "1.5rem",
            cursor: "zoom-out",
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              maxWidth: "92vw",
              maxHeight: "90vh",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              position: "relative",
            }}
          >
            <button
              type="button"
              onClick={() => setPreviewImage(null)}
              style={{
                position: "absolute",
                top: "-2.5rem",
                right: 0,
                background: "transparent",
                border: "none",
                color: "#ffffff",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "0.3rem",
                fontSize: "0.85rem",
              }}
            >
              <X size={20} /> Cerrar
            </button>
            <img
              src={previewImage.src}
              alt={previewImage.alt}
              style={{
                maxWidth: "100%",
                maxHeight: "80vh",
                borderRadius: "var(--radius-md)",
                boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
                objectFit: "contain",
              }}
            />
            <p style={{ color: "#e2e8f0", fontSize: "0.85rem", marginTop: "0.75rem", textAlign: "center" }}>
              {previewImage.caption}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
