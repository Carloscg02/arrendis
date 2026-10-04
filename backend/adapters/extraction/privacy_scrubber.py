import re


class PrivacyScrubber:
    """Servicio de anonimización de datos personales (PII) antes del envío a LLMs.

    Garantiza el principio de minimización de datos del RGPD (Art. 5.1.c) conservando
    intactos los datos técnicos requeridos para la extracción (CUPS, importes, fechas).
    """

    _DNI_REGEX = re.compile(r'\b\d{8}[A-HJ-NP-TV-Z]\b', re.IGNORECASE)
    _NIE_REGEX = re.compile(r'\b[XYZ]\d{7}[A-Z]\b', re.IGNORECASE)
    _CIF_REGEX = re.compile(r'\b[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]\b', re.IGNORECASE)
    _IBAN_REGEX = re.compile(r'\bES\d{2}(?:[\s\-]?\d){20}\b', re.IGNORECASE)
    _MASKED_ACCOUNT_REGEX = re.compile(r'\*{1,}\d{4}')

    _SAFE_KEYWORDS = [
        'cups', 'total factura', 'nº de factura', 'nº de contrato',
        'fecha de emisión', 'periodo de facturación', 'término fijo',
        'energía', 'servicios', 'otros conceptos', 'impuestos', 'consumo',
        'forma de pago', 'fecha de cobro', 'otras vías', 'e-mail',
        'incidencias', 'asistencia', 'portal de consumo', 'información al cliente',
        'peajes de transporte', 'cuota de comercialización', 'potencia contratada',
        'fecha fin de contrato', 'permanencia de contrato', 'distribuidora',
        'peaje de transporte', 'segmentos de cargos', 'nº de contador',
        'nº contrato de acceso', 'tipo de tarifa', 'comercializadora',
        'concepto', 'importe', 'días facturados'
    ]

    _PII_HEADERS = [
        'nombre y apellidos', 'esta es tu factura de', 'titular y datos de pago',
        'dirección de suministro', 'dirección postal', 'cuenta bancaria',
        'localizador de pago', 'dni'
    ]

    @classmethod
    def _apply_inline_redactions(cls, text: str) -> str:
        processed = cls._IBAN_REGEX.sub('[REDACTED_IBAN]', text)
        processed = cls._DNI_REGEX.sub('[REDACTED_NIF]', processed)
        processed = cls._NIE_REGEX.sub('[REDACTED_NIF]', processed)
        processed = cls._CIF_REGEX.sub('[REDACTED_NIF]', processed)
        processed = cls._MASKED_ACCOUNT_REGEX.sub('[REDACTED_IBAN]', processed)
        return processed

    @classmethod
    def scrub(cls, raw_text: str) -> str:
        """Anonimiza PII en el texto respetando los datos técnicos y fiscales."""
        lines = raw_text.splitlines()
        scrubbed_lines: list[str] = []
        redacting_section = False
        last_header: list[str] = []

        for line in lines:
            stripped = line.strip()
            lower = stripped.lower()

            # Si encontramos una palabra clave técnica segura, salimos del modo redacción
            if any(lower.startswith(k) for k in cls._SAFE_KEYWORDS):
                redacting_section = False

            if redacting_section:
                if stripped == '':
                    redacting_section = False
                    scrubbed_lines.append(line)
                else:
                    scrubbed_lines.append('[REDACTED_PII]')
                    # Si el encabezado era de valor de una sola línea, resetear
                    if any(h in ['dni', 'cuenta bancaria'] for h in last_header):
                        redacting_section = False
                continue

            # Comprobar si la línea es un encabezado de PII
            matched_header = [h for h in cls._PII_HEADERS if lower.startswith(h)]
            if matched_header:
                last_header = matched_header
                scrubbed_lines.append(cls._apply_inline_redactions(stripped))
                redacting_section = True
                continue

            scrubbed_lines.append(cls._apply_inline_redactions(stripped))

        return "\n".join(scrubbed_lines)
