"""
Tests unitarios para PrivacyScrubber (F-18 / GDPR Compliance).

Verifica la anonimización de datos personales (PII) antes de invocar a modelos LLM,
asegurando el principio de minimización de datos del RGPD.
"""

from backend.domain.extraction import PrivacyScrubber


def test_privacy_scrubber_redacts_dni():
    """UT-F18-01: Redacta DNI español."""
    raw = "DNI del titular: 53918290B en la factura."
    scrubbed = PrivacyScrubber.scrub(raw)
    assert "53918290B" not in scrubbed
    assert "[REDACTED_NIF]" in scrubbed


def test_privacy_scrubber_redacts_nie_and_cif():
    """UT-F18-02: Redacta NIE y CIF sin alterar otros textos."""
    raw = "NIE: X1234567L y CIF: B39540760."
    scrubbed = PrivacyScrubber.scrub(raw)
    assert "X1234567L" not in scrubbed
    assert "B39540760" not in scrubbed
    assert scrubbed.count("[REDACTED_NIF]") == 2


def test_privacy_scrubber_redacts_iban_and_masked_accounts():
    """UT-F18-03: Redacta cuenta enmascarada (*3940) e IBAN español."""
    raw = "Cuenta bancaria: *3940. IBAN: ES91 2100 0418 45 0200051332."
    scrubbed = PrivacyScrubber.scrub(raw)
    assert "*3940" not in scrubbed
    assert "ES91 2100 0418 45 0200051332" not in scrubbed
    assert "[REDACTED_IBAN]" in scrubbed


def test_privacy_scrubber_preserves_cups():
    """UT-F18-04: No altera el código CUPS bajo ninguna circunstancia."""
    raw = (
        "CUPS\n"
        "ES0031103721971011PR0F\n"
        "Total factura\n"
        "75,46 €"
    )
    scrubbed = PrivacyScrubber.scrub(raw)
    assert "ES0031103721971011PR0F" in scrubbed
    assert "75,46 €" in scrubbed


def test_privacy_scrubber_redacts_multiline_pii_headers():
    """UT-F18-05: Redacta líneas tras encabezados de PII (nombre, dirección)."""
    raw = (
        "Factura de luz\n"
        "Esta es tu factura de luz,\n"
        "Alvaro Heredia Casado\n"
        "CUPS\n"
        "ES0031103721971011PR0F\n"
        "Dirección de suministro\n"
        "CL FRANK CAPRA 4 3\n"
        "6 A 29010 MÁLAGA\n"
        "Total factura\n"
        "75,46 €"
    )
    scrubbed = PrivacyScrubber.scrub(raw)
    assert "Alvaro Heredia Casado" not in scrubbed
    assert "CL FRANK CAPRA" not in scrubbed
    assert "ES0031103721971011PR0F" in scrubbed
    assert "75,46 €" in scrubbed


def test_privacy_scrubber_preserves_amounts_and_dates():
    """UT-F18-06: Preserva importes monetarios, fechas y conceptos técnicos."""
    raw = (
        "Fecha de emisión\n"
        "01/08/2026\n"
        "Total factura\n"
        "75,46 €\n"
        "Periodo de facturación\n"
        "28/06/2026 - 28/07/2026\n"
        "Consumo en este periodo\n"
        "354,50 kWh"
    )
    scrubbed = PrivacyScrubber.scrub(raw)
    assert "01/08/2026" in scrubbed
    assert "75,46 €" in scrubbed
    assert "28/06/2026 - 28/07/2026" in scrubbed
    assert "354,50 kWh" in scrubbed
