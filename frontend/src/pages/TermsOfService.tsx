import { Link } from 'react-router-dom';
import { ArrowLeft, FileText } from 'lucide-react';
import ArrendisLogo from '../components/ArrendisLogo';

export default function TermsOfService() {
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
            <FileText size={14} className="text-[var(--brand-burgundy)]" />
            <span>CONDICIONES GENERALES DE CONTRATACIÓN Y USO</span>
          </div>
          <h1 className="font-serif text-3xl sm:text-4xl text-[var(--text-primary)] font-medium tracking-tight">
            Términos y Condiciones de Uso
          </h1>
          <p className="mt-2 text-xs font-mono text-[var(--text-secondary)]">
            Última actualización: 03 de octubre de 2026 · Versión 1.0 (LSSI-CE Ley 34/2002)
          </p>
        </div>

        {/* Early Access Notice Banner */}
        <div className="mb-8 rounded-sm border border-[var(--panel-border)] bg-[var(--bg-secondary)] p-4 text-xs text-[var(--text-secondary)] leading-relaxed">
          <span className="font-mono font-semibold text-[var(--text-primary)] uppercase tracking-wider block mb-1">
            Versión Preliminar (Early Access)
          </span>
          La plataforma web Arrendis se ofrece en modalidad de acceso preliminar. El usuario reconoce y
          acepta que el software se encuentra en evolución continua y que se proporciona "tal cual" y
          "según disponibilidad", sin garantías expresas sobre la infalibilidad ininterrumpida de sus servicios.
        </div>

        {/* Legal Body Sections */}
        <div className="space-y-8 text-sm text-[var(--text-secondary)] leading-relaxed">
          <section className="space-y-3">
            <h2 className="font-serif text-xl text-[var(--text-primary)] font-medium">
              1. Identificación del Titular del Servicio
            </h2>
            <p>
              En cumplimiento del artículo 10 de la Ley 34/2002 (LSSI-CE), se informa a los usuarios de que
              la titularidad de este sitio web corresponde a:
            </p>
            <ul className="list-disc pl-5 space-y-1 font-mono text-xs text-[var(--text-primary)]">
              <li><strong>Titular / Razón Social:</strong> [Razón Social / Titular de la Plataforma]</li>
              <li><strong>NIF / CIF:</strong> [NIF/CIF del Responsable]</li>
              <li><strong>Domicilio a efectos de notificaciones:</strong> [Dirección Postal de Contacto]</li>
              <li><strong>Correo de Contacto y Soporte:</strong> soporte@arrendis.com</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="font-serif text-xl text-[var(--text-primary)] font-medium">
              2. Objeto de la Plataforma
            </h2>
            <p>
              Arrendis es una aplicación de software diseñada como herramienta de organización, control y
              simulación para propietarios de inmuebles en régimen de alquiler en España. Sus funcionalidades
              incluyen el registro de contratos de arrendamiento, la centralización de recibos de suministros
              y la simulación del cálculo del rendimiento neto y amortización en el Impuesto sobre la Renta de
              las Personas Físicas (IRPF).
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-serif text-xl text-[var(--text-primary)] font-medium">
              3. Registro de Cuenta y Responsabilidad de Acceso
            </h2>
            <p>
              Para acceder a las funcionalidades de gestión es imprescindible el registro previo. El usuario
              se compromete a facilitar información veraz y a custodiar sus claves de acceso con la debida
              diligencia, asumiendo la responsabilidad plena por las actividades que se realicen bajo sus
              credenciales de autenticación.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-serif text-xl text-[var(--text-primary)] font-medium">
              4. Uso Aceptable y Prohibición de Abuso
            </h2>
            <p>
              Queda expresamente prohibido:
            </p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Realizar ataques de denegación de servicio, saturación o ataques automatizados de fuerza bruta.</li>
              <li>Extraer masivamente datos mediante técnicas de scraping no autorizadas.</li>
              <li>Introducir información falsa, fraudulenta o de terceros sin la debida habilitación legal.</li>
              <li>Intentar descompilar, revertir o vulnerar las medidas de seguridad del backend o de la API.</li>
            </ul>
          </section>

          <section className="space-y-3 border-l-2 border-[var(--brand-burgundy)] pl-4 py-1 bg-[var(--bg-secondary)] p-4 rounded-sm">
            <h2 className="font-serif text-xl text-[var(--text-primary)] font-medium">
              5. Exención Expresa de Responsabilidad sobre Cálculos Fiscales y Borradores AEAT
            </h2>
            <p className="font-semibold text-[var(--text-primary)]">
              Por favor, lea con especial atención la siguiente estipulación:
            </p>
            <p>
              <strong>Arrendis es única y exclusivamente una solución de software tecnológico de apoyo y simulación analítica.</strong> Todos
              los cálculos generados por la plataforma —incluyendo, sin carácter limitativo, los porcentajes de amortización
              (Art. 23 de la Ley del IRPF), los rendimientos netos del capital inmobiliario, las reducciones autonómicas o
              estatales y la asignación orientativa de casillas del Modelo 100 de IRPF— constituyen
              <strong> simulaciones algorítmicas de carácter estrictamente informativo y orientativo</strong>.
            </p>
            <p>
              <strong>Arrendis no es una gestoría administrativa, ni una asesoría fiscal, tributaria o jurídica colegiada.</strong> La
              exactitud y adecuación legal de cualquier cálculo dependen indefectiblemente de la integridad, actualidad y
              veracidad de los datos contables y catastrales introducidos por el usuario.
            </p>
            <p>
              <strong>Responsabilidad exclusiva del usuario:</strong> La decisión de utilizar los borradores o datos de
              Arrendis ante la Agencia Estatal de Administración Tributaria (AEAT) o cualquier organismo público recae
              de manera exclusiva, personal e indelegable en el usuario. Se recomienda expresamente contrastar siempre
              los resultados y simulaciones con un <strong>asesor fiscal cualificado y debidamente colegiado</strong> antes
              de la presentación formal de cualquier autoliquidación o declaración tributaria.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-serif text-xl text-[var(--text-primary)] font-medium">
              6. Propiedad Intelectual
            </h2>
            <p>
              El código fuente, los diseños de interfaz Atelier Editorial, marcas, algoritmos y documentación
              técnica de Arrendis son propiedad exclusiva de sus titulares legítimos y se encuentran protegidos
              por las leyes de propiedad intelectual e industrial aplicables.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-serif text-xl text-[var(--text-primary)] font-medium">
              7. Ley Aplicable y Jurisdicción
            </h2>
            <p>
              Las presentes Condiciones se regirán e interpretarán de conformidad con la legislación española.
              Para la resolución de cualquier controversia o litigio que pudiera derivarse del uso de la
              plataforma, las partes se someten expresamente a los juzgados y tribunales de la ciudad correspondiente
              al domicilio del titular, con renuncia a cualquier otro fuero que pudiera corresponderles, sin perjuicio
              de los derechos que asistan a los usuarios en su condición de consumidores conforme al Real Decreto
              Legislativo 1/2007.
            </p>
          </section>
        </div>

        {/* Editorial Footer Note */}
        <div className="mt-12 border-t border-[var(--panel-border)] pt-6 flex flex-col sm:flex-row justify-between items-center text-xs text-[var(--text-muted)] font-mono gap-4">
          <span>© 2026 Arrendis · Atelier Editorial</span>
          <div className="flex gap-4">
            <Link to="/privacy" className="hover:text-[var(--text-primary)] transition-colors">
              Política de Privacidad
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
