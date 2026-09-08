import { useState, useRef, useEffect } from "react";
import { 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Trash2, 
  Loader2, 
  ArrowRight,
  Mail,
  ShieldCheck
} from "lucide-react";
import Modal from "./Modal";
import { uploadUtilityInvoices, getForwardingEmail, updateForwardingEmail } from "../services/api";
import { useAuth } from "./AuthProvider";
import GmailForwardingGuide from "./GmailForwardingGuide";
import type { BatchInvoiceUploadResponse, InvoiceUploadItemResult } from "../types";

interface InvoiceUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  initialTab?: 'upload' | 'email';
}

export default function InvoiceUploadModal({
  isOpen,
  onClose,
  onSuccess,
  initialTab = 'upload',
}: InvoiceUploadModalProps) {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'upload' | 'email'>(initialTab);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<BatchInvoiceUploadResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [hasImported, setHasImported] = useState(false);

  // Email Ingestion Automation State
  const [inboundAddress, setInboundAddress] = useState<string>('facturas@arrendis.com');
  const [forwardingEmailInput, setForwardingEmailInput] = useState<string>('');
  const [isSavingEmail, setIsSavingEmail] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      if (initialTab) setActiveTab(initialTab);
      getForwardingEmail()
        .then((res) => {
          if (res.inbound_address) setInboundAddress(res.inbound_address);
          if (res.forwarding_email) setForwardingEmailInput(res.forwarding_email);
        })
        .catch(() => {});
    }
  }, [isOpen, initialTab]);

  const resetState = () => {
    setSelectedFiles([]);
    setIsDragging(false);
    setIsProcessing(false);
    setResult(null);
    setErrorMessage(null);
    setActiveTab('upload');
    setSaveMessage(null);
    setHasImported(false);
  };

  const handleSaveForwardingEmail = async () => {
    setIsSavingEmail(true);
    setSaveMessage(null);
    try {
      const res = await updateForwardingEmail(forwardingEmailInput.trim() || null);
      setForwardingEmailInput(res.forwarding_email || '');
      setSaveMessage('Guardado correctamente');
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (err: any) {
      setSaveMessage(err.message || 'Error al guardar email');
    } finally {
      setIsSavingEmail(false);
    }
  };

  const handleClose = () => {
    const wasImported = hasImported || (result && result.successful_count > 0);
    onClose();
    if (wasImported) {
      onSuccess();
    }
    setTimeout(() => {
      resetState();
    }, 200);
  };

  const handleFilesAdded = (files: FileList | File[]) => {
    const pdfFiles = Array.from(files).filter(
      (f) => f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf")
    );
    if (pdfFiles.length === 0) {
      setErrorMessage("Por favor selecciona archivos en formato PDF.");
      return;
    }
    setErrorMessage(null);
    setSelectedFiles((prev) => [...prev, ...pdfFiles]);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesAdded(e.dataTransfer.files);
    }
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUploadAndProcess = async () => {
    if (selectedFiles.length === 0) return;
    setIsProcessing(true);
    setErrorMessage(null);

    try {
      const response = await uploadUtilityInvoices(selectedFiles);
      setResult(response);
      if (response.successful_count > 0) {
        setHasImported(true);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Ocurrió un error al procesar las facturas.");
    } finally {
      setIsProcessing(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={handleClose} 
      title={activeTab === "email" ? "Automatización con Reenvío de Facturas" : "Importar Facturas de Suministros"}
      maxWidth={activeTab === "email" ? "740px" : "580px"}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        {/* Tab Switcher */}
        {!result && (
          <div style={{ display: "flex", gap: "0.5rem", borderBottom: "1px solid var(--panel-border)", paddingBottom: "0.5rem" }}>
            <button
              type="button"
              onClick={() => setActiveTab("upload")}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.4rem",
                padding: "0.4rem 0.85rem",
                borderRadius: "var(--radius-md)",
                fontSize: "0.85rem",
                fontWeight: activeTab === "upload" ? 600 : 500,
                backgroundColor: activeTab === "upload" ? "var(--bg-tertiary)" : "transparent",
                color: activeTab === "upload" ? "var(--text-primary)" : "var(--text-secondary)",
                border: "none",
                cursor: "pointer",
              }}
            >
              <UploadCloud size={15} />
              Subir Archivos PDF
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("email")}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.4rem",
                padding: "0.4rem 0.85rem",
                borderRadius: "var(--radius-md)",
                fontSize: "0.85rem",
                fontWeight: activeTab === "email" ? 600 : 500,
                backgroundColor: activeTab === "email" ? "var(--bg-tertiary)" : "transparent",
                color: activeTab === "email" ? "var(--text-primary)" : "var(--text-secondary)",
                border: "none",
                cursor: "pointer",
              }}
            >
              <Mail size={15} />
              Reenvío por Email
            </button>
          </div>
        )}

        {!result ? (
          activeTab === "upload" ? (
            <>
              <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", margin: 0 }}>
                Sube una o varias facturas en PDF (luz, gas o agua). Se extraerán automáticamente los datos mediante el CUPS y se contabilizarán en tu propiedad.
              </p>

              {/* Drop Zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                style={{
                  border: `2px dashed ${isDragging ? "var(--accent-secondary)" : "var(--panel-border)"}`,
                  backgroundColor: isDragging ? "var(--bg-tertiary)" : "var(--bg-primary)",
                  borderRadius: "var(--radius-lg)",
                  padding: "2rem 1.5rem",
                  textAlign: "center",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: "0.75rem",
                }}
              >
                <div
                  style={{
                    width: "48px",
                    height: "48px",
                    borderRadius: "50%",
                    backgroundColor: "var(--bg-secondary)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "var(--accent-secondary)",
                    boxShadow: "var(--shadow-card)",
                  }}
                >
                  <UploadCloud size={24} />
                </div>
                <div>
                  <p style={{ fontWeight: 500, color: "var(--text-primary)", margin: "0 0 0.25rem 0" }}>
                    Arrastra tus archivos PDF aquí
                  </p>
                  <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", margin: 0 }}>
                    o haz clic para explorar tus carpetas (admite selección múltiple)
                  </p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,application/pdf"
                  style={{ display: "none" }}
                  onChange={(e) => {
                    if (e.target.files) handleFilesAdded(e.target.files);
                    e.target.value = "";
                  }}
                />
              </div>

              {/* Selected files list */}
              {selectedFiles.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "0.85rem", fontWeight: 500, color: "var(--text-secondary)" }}>
                      Archivos seleccionados ({selectedFiles.length})
                    </span>
                    <button
                      type="button"
                      onClick={() => setSelectedFiles([])}
                      style={{
                        background: "none",
                        border: "none",
                        fontSize: "0.8rem",
                        color: "var(--danger)",
                        cursor: "pointer",
                        padding: "0.2rem 0.4rem",
                      }}
                    >
                      Limpiar todo
                    </button>
                  </div>

                  <div
                    style={{
                      maxHeight: "180px",
                      overflowY: "auto",
                      display: "flex",
                      flexDirection: "column",
                      gap: "0.4rem",
                      paddingRight: "0.25rem",
                    }}
                  >
                    {selectedFiles.map((file, idx) => (
                      <div
                        key={`${file.name}-${idx}`}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          padding: "0.5rem 0.75rem",
                          backgroundColor: "var(--bg-tertiary)",
                          borderRadius: "var(--radius-md)",
                          fontSize: "0.85rem",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", overflow: "hidden" }}>
                          <FileText size={16} style={{ color: "var(--text-secondary)", flexShrink: 0 }} />
                          <span
                            style={{
                              whiteSpace: "nowrap",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              maxWidth: "280px",
                              fontWeight: 500,
                            }}
                            title={file.name}
                          >
                            {file.name}
                          </span>
                          <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
                            ({formatFileSize(file.size)})
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRemoveFile(idx);
                          }}
                          style={{
                            background: "none",
                            border: "none",
                            color: "var(--text-muted)",
                            cursor: "pointer",
                            display: "flex",
                            alignItems: "center",
                            padding: "0.2rem",
                          }}
                          title="Quitar archivo"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {errorMessage && (
                <div
                  style={{
                    padding: "0.75rem 1rem",
                    backgroundColor: "var(--toast-error-bg)",
                    border: "1px solid #fecaca",
                    borderRadius: "var(--radius-md)",
                    color: "var(--danger)",
                    fontSize: "0.85rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  <AlertCircle size={16} style={{ flexShrink: 0 }} />
                  <span>{errorMessage}</span>
                </div>
              )}

              {/* Automation Discovery Prompt in Upload Tab */}
              <div
                style={{
                  padding: "0.65rem 0.85rem",
                  backgroundColor: "var(--bg-tertiary)",
                  border: "1px solid var(--panel-border)",
                  borderRadius: "var(--radius-md)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "0.75rem",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <Mail size={14} style={{ color: "var(--text-secondary)", flexShrink: 0 }} />
                  <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                    ¿Prefieres automatizarlo? Reenvía tus facturas a <code style={{ fontFamily: "monospace", fontSize: "0.8rem", color: "var(--text-primary)", backgroundColor: "var(--bg-secondary)", padding: "0.1rem 0.3rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--panel-border)" }}>{inboundAddress}</code>
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setActiveTab("email")}
                  style={{
                    background: "none",
                    border: "none",
                    color: "var(--accent-secondary, #2563eb)",
                    fontSize: "0.8rem",
                    fontWeight: 600,
                    cursor: "pointer",
                    whiteSpace: "nowrap",
                    padding: 0,
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.25rem",
                  }}
                >
                  Configurar <ArrowRight size={12} />
                </button>
              </div>

              {/* Actions */}
              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "0.5rem" }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleClose}
                  disabled={isProcessing}
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleUploadAndProcess}
                  disabled={selectedFiles.length === 0 || isProcessing}
                  style={{ minWidth: "150px" }}
                >
                  {isProcessing ? (
                    <>
                      <Loader2 size={16} className="animate-spin" style={{ marginRight: "0.5rem" }} />
                      Procesando...
                    </>
                  ) : (
                    <>
                      <ArrowRight size={16} style={{ marginRight: "0.4rem" }} />
                      Procesar {selectedFiles.length > 0 ? `(${selectedFiles.length})` : ""}
                    </>
                  )}
                </button>
              </div>
            </>
          ) : (
            /* Email Tab */
            <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              <div>
                <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)", margin: "0 0 0.25rem 0" }}>
                  Automatización con reenvío de facturas (Gmail)
                </h3>
                <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", margin: 0, lineHeight: 1.5 }}>
                  Configura una regla en Gmail una única vez. Tus facturas se importarán y contabilizarán automáticamente al recibirlas, sin descargas manuales ni intervención.
                </p>
              </div>

              {/* Interactive Step-by-Step Visual Guide with Real Screenshots */}
              <GmailForwardingGuide inboundAddress={inboundAddress} />

              {/* Anti-Spoofing & Sender Configuration */}
              <div
                style={{
                  padding: "0.85rem 1rem",
                  backgroundColor: "var(--bg-secondary)",
                  border: "1px solid var(--panel-border)",
                  borderRadius: "var(--radius-md)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.75rem",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  <ShieldCheck size={16} style={{ color: "var(--text-secondary)" }} />
                  <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)" }}>
                    Seguridad y Remitente Autorizado
                  </span>
                </div>
                <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: 0, lineHeight: 1.4 }}>
                  Por seguridad anti-spoofing, el sistema solo procesa correos procedentes de tu email de cuenta o de la dirección de reenvío autorizada que indiques aquí.
                </p>

                <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Email de cuenta: <strong style={{ color: "var(--text-secondary)" }}>{user?.email || "cargando..."}</strong> (autorizado)
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                  <label style={{ fontSize: "0.8rem", fontWeight: 500, color: "var(--text-secondary)" }}>
                    Email alternativo donde recibes las facturas (opcional):
                  </label>
                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    <input
                      type="email"
                      placeholder="ej. facturas.personales@gmail.com"
                      value={forwardingEmailInput}
                      onChange={(e) => setForwardingEmailInput(e.target.value)}
                      style={{
                        flex: 1,
                        fontSize: "0.85rem",
                        padding: "0.4rem 0.6rem",
                        borderRadius: "var(--radius-md)",
                        border: "1px solid var(--panel-border)",
                        backgroundColor: "var(--bg-primary)",
                        color: "var(--text-primary)",
                      }}
                    />
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={handleSaveForwardingEmail}
                      disabled={isSavingEmail}
                      style={{ fontSize: "0.8rem", padding: "0.4rem 0.85rem", flexShrink: 0 }}
                    >
                      {isSavingEmail ? "Guardando..." : "Guardar"}
                    </button>
                  </div>
                  {saveMessage && (
                    <span style={{ fontSize: "0.75rem", color: saveMessage.includes("Error") ? "var(--danger)" : "var(--success)" }}>
                      {saveMessage}
                    </span>
                  )}
                </div>
              </div>

              {/* Explicit Legal Consent (GDPR Mandatory) */}
              <div
                style={{
                  padding: "0.75rem 0.85rem",
                  backgroundColor: "var(--bg-tertiary)",
                  border: "1px solid var(--panel-border)",
                  borderRadius: "var(--radius-md)",
                  fontSize: "0.75rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.45,
                }}
              >
                <strong style={{ color: "var(--text-primary)" }}>Consentimiento de procesamiento:</strong>
                <p style={{ margin: "0.25rem 0 0 0", fontStyle: "italic" }}>
                  "Al reenviar correos a esta dirección, autorizas el procesamiento automatizado del documento para extraer los datos de la factura."
                </p>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.5rem" }}>
                <button type="button" className="btn btn-secondary" onClick={handleClose}>
                  Cerrar
                </button>
              </div>
            </div>
          )
        ) : (
          /* Results View */
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {/* KPI Summary Header */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
                gap: "0.75rem",
              }}
            >
              <div
                style={{
                  padding: "0.85rem 1rem",
                  backgroundColor: "#f0fdf4",
                  border: "1px solid #bbf7d0",
                  borderRadius: "var(--radius-md)",
                }}
              >
                <div style={{ fontSize: "0.75rem", color: "#166534", fontWeight: 500 }}>Importadas</div>
                <div style={{ fontSize: "1.25rem", fontWeight: 600, color: "#15803d" }}>
                  {result.successful_count}
                </div>
                {result.successful_count > 0 && (
                  <div style={{ fontSize: "0.75rem", color: "#166534", marginTop: "0.2rem" }}>
                    Total: {parseFloat(String(result.total_amount_imported || 0)).toFixed(2)} €
                  </div>
                )}
              </div>

              {result.duplicate_count > 0 && (
                <div
                  style={{
                    padding: "0.85rem 1rem",
                    backgroundColor: "#fffbeb",
                    border: "1px solid #fde68a",
                    borderRadius: "var(--radius-md)",
                  }}
                >
                  <div style={{ fontSize: "0.75rem", color: "#92400e", fontWeight: 500 }}>Duplicadas</div>
                  <div style={{ fontSize: "1.25rem", fontWeight: 600, color: "#b45309" }}>
                    {result.duplicate_count}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#92400e", marginTop: "0.2rem" }}>
                    Omitidas
                  </div>
                </div>
              )}

              {result.error_count > 0 && (
                <div
                  style={{
                    padding: "0.85rem 1rem",
                    backgroundColor: "#fef2f2",
                    border: "1px solid #fecaca",
                    borderRadius: "var(--radius-md)",
                  }}
                >
                  <div style={{ fontSize: "0.75rem", color: "#991b1b", fontWeight: 500 }}>Con Errores</div>
                  <div style={{ fontSize: "1.25rem", fontWeight: 600, color: "#b91c1c" }}>
                    {result.error_count}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#991b1b", marginTop: "0.2rem" }}>
                    Revisar
                  </div>
                </div>
              )}
            </div>

            {/* Automation Discovery Tip Banner */}
            <div
              style={{
                padding: "0.85rem 1rem",
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--panel-border)",
                borderRadius: "var(--radius-md)",
                display: "flex",
                alignItems: "flex-start",
                gap: "0.75rem",
              }}
            >
              <div
                style={{
                  width: "28px",
                  height: "28px",
                  borderRadius: "var(--radius-sm)",
                  backgroundColor: "var(--bg-secondary)",
                  border: "1px solid var(--panel-border)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--text-primary)",
                  flexShrink: 0,
                  marginTop: "1px",
                }}
              >
                <Mail size={15} />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem", flex: 1 }}>
                <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)" }}>
                  ¿Sabías que puedes automatizar esto?
                </div>
                <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: 0, lineHeight: 1.45 }}>
                  Configura el envío de facturas a{" "}
                  <code
                    style={{
                      fontFamily: "monospace",
                      fontWeight: 600,
                      fontSize: "0.8rem",
                      backgroundColor: "var(--bg-secondary)",
                      padding: "0.1rem 0.35rem",
                      borderRadius: "var(--radius-sm)",
                      border: "1px solid var(--panel-border)",
                      color: "var(--text-primary)",
                    }}
                  >
                    {inboundAddress}
                  </code>{" "}
                  o crea una regla de reenvío en tu correo. El sistema las asignará automáticamente a tu propiedad mediante el CUPS.
                </p>
                <div style={{ marginTop: "0.25rem" }}>
                  <button
                    type="button"
                    onClick={() => {
                      setResult(null);
                      setActiveTab("email");
                    }}
                    style={{
                      background: "none",
                      border: "none",
                      padding: 0,
                      color: "var(--accent-secondary, #2563eb)",
                      fontSize: "0.8rem",
                      fontWeight: 600,
                      cursor: "pointer",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.35rem",
                    }}
                  >
                    <span>Configurar regla de reenvío</span>
                    <ArrowRight size={13} />
                  </button>
                </div>
              </div>
            </div>

            {/* List of item details */}
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              <span style={{ fontSize: "0.85rem", fontWeight: 500, color: "var(--text-secondary)" }}>
                Detalle del lote ({result.items.length})
              </span>
              <div
                style={{
                  maxHeight: "220px",
                  overflowY: "auto",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.5rem",
                  paddingRight: "0.25rem",
                }}
              >
                {result.items.map((item: InvoiceUploadItemResult, index: number) => (
                  <div
                    key={index}
                    style={{
                      padding: "0.75rem 1rem",
                      borderRadius: "var(--radius-md)",
                      backgroundColor:
                        item.status === "success"
                          ? "var(--bg-secondary)"
                          : item.status === "duplicate"
                          ? "#fffdf5"
                          : "#fff8f8",
                      border: `1px solid ${
                        item.status === "success"
                          ? "var(--panel-border)"
                          : item.status === "duplicate"
                          ? "#fef3c7"
                          : "#fee2e2"
                      }`,
                      display: "flex",
                      flexDirection: "column",
                      gap: "0.25rem",
                      fontSize: "0.85rem",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontWeight: 500 }}>
                        {item.status === "success" ? (
                          <CheckCircle2 size={16} style={{ color: "#16a34a" }} />
                        ) : item.status === "duplicate" ? (
                          <AlertCircle size={16} style={{ color: "#d97706" }} />
                        ) : (
                          <AlertCircle size={16} style={{ color: "#dc2626" }} />
                        )}
                        <span>{item.filename}</span>
                      </div>

                      {item.status === "success" && item.amount !== undefined && item.amount !== null && (
                        <span style={{ fontWeight: 600, color: "#15803d", fontVariantNumeric: "tabular-nums" }}>
                          +{parseFloat(String(item.amount)).toFixed(2)} €
                        </span>
                      )}
                    </div>

                    {item.status === "success" && (
                      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", color: "var(--text-secondary)", fontSize: "0.8rem", paddingLeft: "1.4rem" }}>
                        {item.expense?.utility_data?.provider_name && (
                          <span>{item.expense.utility_data.provider_name}</span>
                        )}
                        {item.property_name && (
                          <span>Inmueble: <strong>{item.property_name}</strong></span>
                        )}
                      </div>
                    )}

                    {item.status === "duplicate" && (
                      <div style={{ color: "#b45309", fontSize: "0.8rem", paddingLeft: "1.4rem" }}>
                        {item.message || "Esta factura ya fue importada previamente para esta propiedad."}
                      </div>
                    )}

                    {item.status === "error" && (
                      <div style={{ color: "#b91c1c", fontSize: "0.8rem", paddingLeft: "1.4rem" }}>
                        {item.message || "Error al procesar el archivo."}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Bottom Button */}
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.5rem" }}>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleClose}
                style={{ width: "100%" }}
              >
                Cerrar y Ver Gastos
              </button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
