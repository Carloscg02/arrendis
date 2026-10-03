import { Link } from 'react-router-dom';
import { ArrowLeft, Shield } from 'lucide-react';
import ArrendisLogo from '../components/ArrendisLogo';

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] antialiased">
      {/* Top Editorial Header */}
      <header className="border-b border-[var(--panel-border)] bg-[var(--bg-secondary)] px-4 py-4 sm:px-8">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors min-h-[44px] min-w-[44px]"
          >
            <ArrowLeft size={16} />
            <span>Volver al Inicio</span>
          </Link>
          <ArrendisLogo size="sm" showSubtitle={false} />
        </div>
      </header>

      {/* Main Content Container */}
      <main className="mx-auto max-w-4xl px-4 py-10 sm:px-8">
        <div className="mb-8 border-b border-[var(--panel-border)] pb-6">
          <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-muted)] mb-2">
            <Shield size={14} className="text-[var(--brand-burgundy)]" />
            <span>MARCO LEGAL Y PROTECCIÓN DE DATOS</span>
          </div>
          <h1 className="font-serif text-3xl sm:text-4xl text-[var(--text-primary)] font-medium tracking-tight">
            Política de Privacidad
          </h1>
          <p className="mt-2 text-xs font-mono text-[var(--text-secondary)]">
            Última actualización: 03 de octubre de 2026 · Versión 1.0 (Conformidad RGPD UE 2016/679)
          </p>
        </div>

        {/* Early Access Notice Banner */}
        <div className="mb-8 rounded-sm border border-[var(--panel-border)] bg-[var(--bg-secondary)] p-4 text-xs text-[var(--text-secondary)] leading-relaxed">
          <span className="font-mono font-semibold text-[var(--text-primary)] uppercase tracking-wider block mb-1">
            Aviso de Versión Preliminar (Early Access)
          </span>
          Arrendis opera actualmente en fase de acceso preliminar. Todos los datos recopilados
          se custodian con estrictas medidas de seguridad técnica (cifrado en tránsito vía TLS/HTTPS,
          hashing de credenciales y cookies de sesión seguras) en pleno cumplimiento de la normativa
          europea de protección de datos personales.
        </div>

        {/* Legal Body Sections */}
        <div className="space-y-8 text-sm text-[var(--text-secondary)] leading-relaxed">
          <section className="space-y-3">
            <h2 className="font-serif text-xl text-[var(--text-primary)] font-medium">
              1. Responsable del Tratamiento
            </h2>
            <p>
              En virtud de lo dispuesto en el Reglamento (UE) 2016/679 (RGPD) y la Ley Orgánica 3/2018
              (LOPDGDD), el usuario queda informado de que los datos personales facilitados a través de
              la plataforma <strong>Arrendis</strong> serán tratados bajo la responsabilidad de:
            </p>
            <ul className="list-disc pl-5 space-y-1 font-mono text-xs text-[var(--text-primary)]">
              <li><strong>Titular / Razón Social:</strong> [Razón Social / Titular de la Plataforma]</li>
              <li><strong>NIF / CIF:</strong> [NIF/CIF del Responsable]</li>
              <li><strong>Domicilio Social:</strong> [Dirección Postal de Contacto]</li>
              <li><strong>Correo de Contacto y Privacidad:</strong> privacidad@arrendis.com</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="font-serif text-xl text-[var(--text-primary)] font-medium">
              2. Categorías de Datos Objeto de Tratamiento
            </h2>
            <p>
              Para prestar los servicios de gestión de carteras inmobiliarias y cálculo fiscal estimativo,
              Arrendis recopila y procesa exclusivamente los datos necesarios aportados por el usuario:
            </p>
            <ul className="list-disc pl-5 space-y-2">
              <li>
                <strong>Datos de cuenta y acceso:</strong> Dirección de correo electrónico, nombre de usuario y
                clave de acceso almacenada de forma irreversible mediante algoritmo criptográfico seguro (bcrypt).
              </li>
              <li>
                <strong>Datos de bienes inmuebles y Catastro:</strong> Dirección postal de las propiedades, referencia
                catastral oficial (20 caracteres), valores catastrales (desglose suelo/construcción), superficie
                construida en m², año y costes de adquisición.
              </li>
              <li>
                <strong>Datos de contratos y partes arrendatarias:</strong> Nombres y apellidos de inquilinos,
                documento identificativo (NIF/NIE), importe de renta pactada, fianza y fechas de inicio y finalización
                del contrato de arrendamiento.
              </li>
              <li>
                <strong>Datos de suministros y facturación:</strong> Códigos Unificados de Punto de Suministro (CUPS),
                importes devengados, fechas de emisión e información extraída de facturas energéticas o de agua.
              </li>
              <li>
                <strong>Datos técnicos y de navegación:</strong> Dirección IP, registros de acceso y cabeceras técnicas,
                utilizados exclusivamente para la prevención de ataques de fuerza bruta y rate limiting defensivo.
              </li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="font-serif text-xl text-[var(--text-primary)] font-medium">
              3. Finalidad y Base Jurídica del Tratamiento
            </h2>
            <p>
              Los datos se tratan con las siguientes finalidades legítimas:
            </p>
            <ul className="list-disc pl-5 space-y-1">
              <li>
                <strong>Ejecución del servicio (Art. 6.1.b RGPD):</strong> Permitir al usuario organizar sus inmuebles,
                centralizar gastos deducibles y generar simulaciones del rendimiento neto y amortización fiscal (Modelo 100).
              </li>
              <li>
                <strong>Seguridad del sistema e interés legítimo (Art. 6.1.f RGPD):</strong> Proteger la infraestructura
                contra accesos no autorizados, abuso de API y ciberataques.
              </li>
            </ul>
            <p>
              Arrendis <strong>no vende, comercializa ni cede</strong> datos personales o patrimoniales a terceros con
              fines publicitarios o de prospección comercial.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-serif text-xl text-[var(--text-primary)] font-medium">
              4. Plazo de Conservación de la Información
            </h2>
            <p>
              Los datos personales se mantendrán activos mientras el usuario mantenga su cuenta en Arrendis. Tras la
              solicitud de baja o cancelación, la información vinculada a deducciones y amortizaciones se conservará
              bloqueada durante un plazo de <strong>5 años</strong>, en estricto cumplimiento de los plazos de
              prescripción legal establecidos en la Ley 58/2003, General Tributaria (LGT) española.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-serif text-xl text-[var(--text-primary)] font-medium">
              5. Ejercicio de Derechos (ARCO+)
            </h2>
            <p>
              El usuario puede ejercer en cualquier momento sus derechos de acceso, rectificación, supresión (derecho al
              olvido), limitación del tratamiento, portabilidad y oposición, remitiendo una solicitud firmada con copia de
              su documento de identidad a:
            </p>
            <p className="font-mono text-xs text-[var(--text-primary)] bg-[var(--bg-secondary)] p-3 border border-[var(--panel-border)] rounded-sm">
              Canal de Protección de Datos: <strong>privacidad@arrendis.com</strong>
            </p>
            <p>
              Asimismo, tiene derecho a interponer una reclamación ante la Agencia Española de Protección de Datos
              (AEPD) en caso de considerar vulnerados sus derechos.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-serif text-xl text-[var(--text-primary)] font-medium">
              6. Medidas de Seguridad de la Información
            </h2>
            <p>
              Arrendis implementa salvaguardas técnicas y organizativas para garantizar la confidencialidad e integridad:
            </p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Cifrado obligatorio de transporte HTTPS con protocolo TLS y cabeceras de seguridad HSTS.</li>
              <li>Aislamiento de cookies con directivas <code>HttpOnly</code>, <code>SameSite=Lax</code> y <code>Secure</code> en entornos de producción.</li>
              <li>Almacenamiento de contraseñas bajo algoritmo de hash robusto (Bcrypt con sal).</li>
              <li>Limitación de frecuencia (*rate limiting*) en endpoints críticos de autenticación.</li>
            </ul>
          </section>
        </div>

        {/* Editorial Footer Note */}
        <div className="mt-12 border-t border-[var(--panel-border)] pt-6 flex flex-col sm:flex-row justify-between items-center text-xs text-[var(--text-muted)] font-mono gap-4">
          <span>© 2026 Arrendis · Atelier Editorial</span>
          <div className="flex gap-4">
            <Link to="/terms" className="hover:text-[var(--text-primary)] transition-colors">
              Términos de Servicio
            </Link>
            <Link to="/" className="hover:text-[var(--text-primary)] transition-colors">
              Inicio
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
