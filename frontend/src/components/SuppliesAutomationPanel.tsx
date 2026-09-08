import { useState, useEffect } from "react";
import {
  Sparkles,
  Mail,
  UploadCloud,
  SlidersHorizontal,
  Info,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import type { Property } from "../types";
import { updatePropertyCups, getForwardingEmail } from "../services/api";
import { useToast } from "./Toast";
import GmailForwardingGuide from "./GmailForwardingGuide";

interface SuppliesAutomationPanelProps {
  property: Property;
  onCupsUpdated: () => void;
  onOpenPdfUpload: () => void;
}

export default function SuppliesAutomationPanel({
  property,
  onCupsUpdated,
  onOpenPdfUpload,
}: SuppliesAutomationPanelProps) {
  const toast = useToast();

  // CUPS State
  const [cupsElectricity, setCupsElectricity] = useState(property.cups_electricity || "");
  const [cupsGas, setCupsGas] = useState(property.cups_gas || "");
  const [cupsWater, setCupsWater] = useState(property.cups_water || "");
  const [isSavingCups, setIsSavingCups] = useState(false);
  const [cupsSuccessMessage, setCupsSuccessMessage] = useState<string | null>(null);
  const [cupsError, setCupsError] = useState<string | null>(null);

  // Email state
  const [inboundAddress, setInboundAddress] = useState("facturas@arrendis.com");
  const [copiedEmail, setCopiedEmail] = useState(false);
  const [showGmailGuide, setShowGmailGuide] = useState(false);

  useEffect(() => {
    setCupsElectricity(property.cups_electricity || "");
    setCupsGas(property.cups_gas || "");
    setCupsWater(property.cups_water || "");
  }, [property.cups_electricity, property.cups_gas, property.cups_water]);

  useEffect(() => {
    getForwardingEmail()
      .then((res) => {
        if (res.inbound_address) setInboundAddress(res.inbound_address);
      })
      .catch(() => {});
  }, []);

  const handleCopyEmail = () => {
    navigator.clipboard.writeText(inboundAddress);
    setCopiedEmail(true);
    setTimeout(() => setCopiedEmail(false), 2000);
  };

  const sanitizeCups = (val: string) => {
    const clean = val.replace(/\s+/g, "").toUpperCase();
    return clean.length > 0 ? clean : null;
  };

  const handleSaveCups = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsSavingCups(true);
    setCupsError(null);
    setCupsSuccessMessage(null);

    const cleanElec = sanitizeCups(cupsElectricity);
    const cleanGas = sanitizeCups(cupsGas);
    const cleanWater = sanitizeCups(cupsWater);

    try {
      await updatePropertyCups(property.id, {
        cups_electricity: cleanElec,
        cups_gas: cleanGas,
        cups_water: cleanWater,
      });
      setCupsSuccessMessage("Códigos CUPS actualizados correctamente.");
      toast.success("Códigos CUPS guardados");
      onCupsUpdated();
      setTimeout(() => setCupsSuccessMessage(null), 3000);
    } catch (err: any) {
      const msg = err.message || "Error al guardar los códigos CUPS.";
      setCupsError(msg);
      toast.error(msg);
    } finally {
      setIsSavingCups(false);
    }
  };

  const hasCupsChanged =
    cupsElectricity.replace(/\s+/g, "").toUpperCase() !== (property.cups_electricity || "") ||
    cupsGas.replace(/\s+/g, "").toUpperCase() !== (property.cups_gas || "") ||
    cupsWater.replace(/\s+/g, "").toUpperCase() !== (property.cups_water || "");

  const hasAnyCupsConfigured = !!(property.cups_electricity || property.cups_gas || property.cups_water);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* 1. Brief Explanation Banner */}
      <div
        style={{
          backgroundColor: "var(--bg-tertiary)",
          border: "1px solid var(--panel-border)",
          borderRadius: "var(--radius-lg)",
          padding: "1.25rem 1.5rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.4rem" }}>
          <Sparkles size={18} style={{ color: "var(--accent-secondary, #2563eb)" }} />
          <h4 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 600, color: "var(--text-primary)" }}>
            Automatización del Registro de Suministros
          </h4>
        </div>

        <p style={{ margin: "0 0 1rem 0", fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.55 }}>
          Contabiliza automáticamente las facturas de luz, gas y agua de este inmueble sin introducirlas a mano.
          Dispones de dos vías a tu elección:
        </p>

        {/* 2 Options Pillars */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "0.85rem",
            marginBottom: "0.85rem",
          }}
        >
          {/* Option A Pillar */}
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--panel-border)",
              borderRadius: "var(--radius-md)",
              padding: "0.95rem 1.1rem",
              display: "flex",
              flexDirection: "column",
              gap: "0.4rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.45rem" }}>
                <Mail size={16} style={{ color: "var(--accent-secondary, #2563eb)" }} />
                <span style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--text-primary)" }}>
                  1. Reenvío Automático por Email
                </span>
              </div>
              <span
                style={{
                  fontSize: "0.7rem",
                  fontWeight: 600,
                  padding: "0.15rem 0.5rem",
                  borderRadius: "var(--radius-pill)",
                  backgroundColor: "rgba(37, 99, 235, 0.08)",
                  color: "var(--accent-secondary, #2563eb)",
                }}
              >
                Cero intervención
              </span>
            </div>
            <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
              Configura una regla en Gmail una única vez. Cuando tu compañía suministradora te mande la factura, se
              reenviará y registrará sola en Arrendis.
            </p>
          </div>

          {/* Option B Pillar */}
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--panel-border)",
              borderRadius: "var(--radius-md)",
              padding: "0.95rem 1.1rem",
              display: "flex",
              flexDirection: "column",
              gap: "0.4rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.45rem" }}>
                <UploadCloud size={16} style={{ color: "var(--success, #16a34a)" }} />
                <span style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--text-primary)" }}>
                  2. Subida Manual de PDFs
                </span>
              </div>
              <span
                style={{
                  fontSize: "0.7rem",
                  fontWeight: 600,
                  padding: "0.15rem 0.5rem",
                  borderRadius: "var(--radius-pill)",
                  backgroundColor: "rgba(22, 163, 74, 0.08)",
                  color: "var(--success, #16a34a)",
                }}
              >
                Lote de archivos
              </span>
            </div>
            <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
              Sube directamente las facturas en PDF descargadas de tu compañía. El extractor inteligente detecta
              importes, fechas y conceptos al instante.
            </p>
          </div>
        </div>

        {/* Prerequisite Callout */}
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: "0.5rem",
            fontSize: "0.8rem",
            color: "var(--text-secondary)",
            paddingTop: "0.4rem",
            borderTop: "1px solid var(--panel-border)",
          }}
        >
          <Info size={15} style={{ flexShrink: 0, marginTop: "2px", color: "var(--accent-secondary, #2563eb)" }} />
          <span>
            <strong>Prerrequisito imprescindible:</strong> Para que el sistema asigne las facturas a este inmueble (por
            correo o por PDF), es necesario que tenga guardado su código CUPS o número de contador a continuación.
          </span>
        </div>
      </div>

      {/* 2. CUPS Configuration Section */}
      <div
        style={{
          border: "1px solid var(--panel-border)",
          borderRadius: "var(--radius-lg)",
          backgroundColor: "var(--bg-secondary)",
          padding: "1.25rem 1.5rem",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "0.5rem",
            flexWrap: "wrap",
            gap: "0.5rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <SlidersHorizontal size={17} style={{ color: "var(--text-primary)" }} />
            <h4 style={{ margin: 0, fontSize: "0.98rem", fontWeight: 600, color: "var(--text-primary)" }}>
              Códigos CUPS de este Inmueble
            </h4>
          </div>
          {hasAnyCupsConfigured ? (
            <span className="badge badge-success" style={{ display: "inline-flex", alignItems: "center", gap: "0.3rem" }}>
              <CheckCircle2 size={12} />
              Suministros vinculados
            </span>
          ) : (
            <span className="badge badge-neutral" style={{ display: "inline-flex", alignItems: "center", gap: "0.3rem" }}>
              <AlertCircle size={12} />
              Pendiente de configurar
            </span>
          )}
        </div>

        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "0 0 1rem 0", lineHeight: 1.45 }}>
          El CUPS identifica de forma única tu contador en la red nacional. Aparece en el encabezado de tus facturas
          habituales.
        </p>

        <form onSubmit={handleSaveCups} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: "1rem",
            }}
          >
            {/* Electricity CUPS */}
            <div className="form-group" style={{ margin: 0 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.25rem" }}>
                <label style={{ margin: 0, fontSize: "0.82rem", fontWeight: 600 }}>CUPS Luz (Electricidad)</label>
                {property.cups_electricity ? (
                  <span style={{ fontSize: "0.7rem", color: "var(--success, #16a34a)", fontWeight: 500 }}>Configurado</span>
                ) : (
                  <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Requerido para luz</span>
                )}
              </div>
              <input
                type="text"
                value={cupsElectricity}
                onChange={(e) => setCupsElectricity(e.target.value.toUpperCase())}
                placeholder="ES0031103721971011PR0F"
                style={{
                  fontFamily: "monospace",
                  textTransform: "uppercase",
                  letterSpacing: "0.04em",
                  fontSize: "0.85rem",
                }}
              />
              <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                20 o 22 caracteres (empieza por ES).
              </span>
            </div>

            {/* Gas CUPS */}
            <div className="form-group" style={{ margin: 0 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.25rem" }}>
                <label style={{ margin: 0, fontSize: "0.82rem", fontWeight: 600 }}>CUPS Gas (Opcional)</label>
                {property.cups_gas ? (
                  <span style={{ fontSize: "0.7rem", color: "var(--success, #16a34a)", fontWeight: 500 }}>Configurado</span>
                ) : (
                  <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Opcional</span>
                )}
              </div>
              <input
                type="text"
                value={cupsGas}
                onChange={(e) => setCupsGas(e.target.value.toUpperCase())}
                placeholder="ES0201..."
                style={{
                  fontFamily: "monospace",
                  textTransform: "uppercase",
                  letterSpacing: "0.04em",
                  fontSize: "0.85rem",
                }}
              />
              <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                Código CUPS de tu suministro de gas natural.
              </span>
            </div>

            {/* Water CUPS / Meter */}
            <div className="form-group" style={{ margin: 0 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.25rem" }}>
                <label style={{ margin: 0, fontSize: "0.82rem", fontWeight: 600 }}>CUPS / Contador Agua (Opcional)</label>
                {property.cups_water ? (
                  <span style={{ fontSize: "0.7rem", color: "var(--success, #16a34a)", fontWeight: 500 }}>Configurado</span>
                ) : (
                  <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Opcional</span>
                )}
              </div>
              <input
                type="text"
                value={cupsWater}
                onChange={(e) => setCupsWater(e.target.value.toUpperCase())}
                placeholder="ES... o número de contador"
                style={{
                  fontFamily: "monospace",
                  textTransform: "uppercase",
                  letterSpacing: "0.04em",
                  fontSize: "0.85rem",
                }}
              />
              <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                CUPS de agua o referencia de contrato/contador.
              </span>
            </div>
          </div>

          {cupsError && (
            <div
              style={{
                padding: "0.6rem 0.85rem",
                backgroundColor: "var(--toast-error-bg)",
                border: "1px solid #fecaca",
                borderRadius: "var(--radius-md)",
                color: "var(--danger)",
                fontSize: "0.8rem",
              }}
            >
              {cupsError}
            </div>
          )}

          {cupsSuccessMessage && (
            <div
              style={{
                padding: "0.6rem 0.85rem",
                backgroundColor: "var(--badge-success-bg, #ecfdf5)",
                border: "1px solid var(--badge-success-border, #a7f3d0)",
                borderRadius: "var(--radius-md)",
                color: "var(--badge-success-text, #047857)",
                fontSize: "0.8rem",
                display: "flex",
                alignItems: "center",
                gap: "0.4rem",
              }}
            >
              <CheckCircle2 size={14} />
              {cupsSuccessMessage}
            </div>
          )}

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", alignItems: "center" }}>
            <button
              type="submit"
              className="btn btn-sm btn-primary"
              disabled={isSavingCups || !hasCupsChanged}
              style={{ minWidth: "130px" }}
            >
              {isSavingCups ? "Guardando..." : hasCupsChanged ? "Guardar Cambios" : "CUPS Actualizados"}
            </button>
          </div>
        </form>
      </div>

      {/* 3. The Two Ingestion Channels Actions */}
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <h4 style={{ margin: 0, fontSize: "0.98rem", fontWeight: 600, color: "var(--text-primary)" }}>
          Canales de Registro
        </h4>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
            gap: "1rem",
          }}
        >
          {/* Card A: Email Forwarding Automation */}
          <div
            style={{
              border: "1px solid var(--panel-border)",
              borderRadius: "var(--radius-lg)",
              backgroundColor: "var(--bg-secondary)",
              padding: "1.25rem",
              display: "flex",
              flexDirection: "column",
              gap: "0.85rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <div
                  style={{
                    width: "32px",
                    height: "32px",
                    borderRadius: "var(--radius-md)",
                    backgroundColor: "rgba(37, 99, 235, 0.08)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "var(--accent-secondary, #2563eb)",
                  }}
                >
                  <Mail size={17} />
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: "0.92rem", color: "var(--text-primary)" }}>
                    Reenvío por Correo
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                    Gmail a Arrendis
                  </div>
                </div>
              </div>
              <span className="badge badge-neutral" style={{ fontSize: "0.72rem" }}>
                Automático
              </span>
            </div>

            <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              Dirección de destino para recibir y procesar tus facturas en PDF:
            </p>

            {/* Email Address Display Box */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--panel-border)",
                borderRadius: "var(--radius-md)",
                padding: "0.45rem 0.75rem",
                gap: "0.5rem",
              }}
            >
              <span
                style={{
                  fontFamily: "monospace",
                  fontWeight: 600,
                  fontSize: "0.88rem",
                  color: "var(--text-primary)",
                  wordBreak: "break-all",
                }}
              >
                {inboundAddress}
              </span>
              <button
                type="button"
                className="btn btn-sm btn-secondary"
                onClick={handleCopyEmail}
                style={{ flexShrink: 0, padding: "0.3rem 0.65rem", fontSize: "0.75rem" }}
              >
                {copiedEmail ? (
                  <>
                    <Check size={13} style={{ color: "var(--success, #16a34a)", marginRight: "0.25rem" }} /> Copiado
                  </>
                ) : (
                  <>
                    <Copy size={13} style={{ marginRight: "0.25rem" }} /> Copiar
                  </>
                )}
              </button>
            </div>

            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
              Esta dirección se autoriza una sola vez en Gmail y procesa facturas para todas tus propiedades con CUPS.
            </div>

            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => setShowGmailGuide(!showGmailGuide)}
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.4rem",
                marginTop: "auto",
                padding: "0.55rem 1rem",
              }}
            >
              {showGmailGuide ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
              {showGmailGuide ? "Ocultar guía de Gmail" : "Ver guía visual paso a paso para Gmail"}
            </button>
          </div>

          {/* Card B: Manual PDF Upload */}
          <div
            style={{
              border: "1px solid var(--panel-border)",
              borderRadius: "var(--radius-lg)",
              backgroundColor: "var(--bg-secondary)",
              padding: "1.25rem",
              display: "flex",
              flexDirection: "column",
              gap: "0.85rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <div
                  style={{
                    width: "32px",
                    height: "32px",
                    borderRadius: "var(--radius-md)",
                    backgroundColor: "rgba(22, 163, 74, 0.08)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "var(--success, #16a34a)",
                  }}
                >
                  <UploadCloud size={17} />
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: "0.92rem", color: "var(--text-primary)" }}>
                    Subida Manual de PDFs
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                    Archivos en tu ordenador
                  </div>
                </div>
              </div>
              <span className="badge badge-neutral" style={{ fontSize: "0.72rem" }}>
                Manual / Lote
              </span>
            </div>

            <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              ¿Tienes facturas descargadas de tu compañía? Puedes subirlas en lote; nuestro analizador inteligente
              detectará el CUPS y las asignará a esta vivienda al momento.
            </p>

            <div
              style={{
                backgroundColor: "var(--bg-tertiary)",
                border: "1px dashed var(--panel-border)",
                borderRadius: "var(--radius-md)",
                padding: "1rem",
                textAlign: "center",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "0.5rem",
              }}
            >
              <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                Arrastra archivos PDF o pulsa el botón para seleccionar
              </span>
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={onOpenPdfUpload}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.4rem",
                  padding: "0.45rem 1rem",
                }}
              >
                <UploadCloud size={15} />
                Importar Facturas PDF
              </button>
            </div>

            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "auto", lineHeight: 1.4 }}>
              Podrás revisar el importe, fecha, base imponible e IVA antes de confirmar el registro.
            </div>
          </div>
        </div>

        {/* Inline Gmail Forwarding Guide Accordion */}
        {showGmailGuide && (
          <div
            style={{
              marginTop: "0.5rem",
              border: "1px solid var(--panel-border)",
              borderRadius: "var(--radius-lg)",
              padding: "1.25rem",
              backgroundColor: "var(--bg-secondary)",
              animation: "fadeIn 0.2s ease-out",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "1rem",
                borderBottom: "1px solid var(--panel-border)",
                paddingBottom: "0.75rem",
              }}
            >
              <div>
                <h4 style={{ margin: 0, fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)" }}>
                  Guía Visual: Configurar Regla de Reenvío en Gmail
                </h4>
                <p style={{ margin: "0.2rem 0 0 0", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                  Sigue estos 3 pasos visuales para automatizar tus facturas para siempre.
                </p>
              </div>
              <button
                type="button"
                className="btn btn-sm btn-secondary"
                onClick={() => setShowGmailGuide(false)}
              >
                Cerrar guía
              </button>
            </div>
            <GmailForwardingGuide inboundAddress={inboundAddress} />
          </div>
        )}
      </div>
    </div>
  );
}
