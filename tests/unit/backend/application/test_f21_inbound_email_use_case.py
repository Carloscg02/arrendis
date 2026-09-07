"""
Tests unitarios para F-21: Ingesta Automática por Email (ProcessInboundEmailUseCase).

Verifica:
- T-F21-UC-01: Remitente autorizado por email principal procesa PDF y crea gasto verificado.
- T-F21-UC-02: Remitente autorizado por forwarding_email procesa PDF correctamente.
- T-F21-UC-03: Remitente no autorizado es rechazado sin procesar (Anti-Spoofing).
- T-F21-UC-04: Factura con CUPS no perteneciente al remitente es rechazada (cups_not_owned).
- T-F21-UC-05: Correo sin adjuntos PDF es marcado como 'ignored'.
- T-F21-UC-06: Factura duplicada es detectada y contabilizada como 'duplicate'.
- T-F21-UC-07: Parser de remitente RFC 2822 limpia formatos complejos ('Nombre <email>').
- T-F21-UC-08: Caso de uso UpdateForwardingEmailUseCase valida y persiste email alternativo.
"""

from pathlib import Path
from decimal import Decimal
import pytest

from backend.domain.entities import (
    Property,
    PropertyType,
    PropertyStatus,
    User,
    ExpenseSource,
    ExpenseCategory,
    FiscalExpenseCategory,
)
from backend.domain.value_objects import Address, Email, PasswordHash
from backend.domain.extraction import UtilityExtractorRegistry, RepsolExtractionStrategy
from backend.adapters.pdf_extractor_adapter import PyMuPDFTextExtractorAdapter
from backend.application.use_cases import (
    ProcessUtilityInvoiceUseCase,
    ProcessInboundEmailUseCase,
    UpdateForwardingEmailUseCase,
)

SAMPLE_PDF_PATH = Path("specs/epics/E-02-suministros/samples/factura_ejemplo_1.pdf")
REPSOL_CUPS = "ES0031103721971011PR0F"


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    return SAMPLE_PDF_PATH.read_bytes()


@pytest.fixture
def utility_use_case(property_repo, expense_repo):
    pdf_extractor = PyMuPDFTextExtractorAdapter()
    registry = UtilityExtractorRegistry([RepsolExtractionStrategy()])
    return ProcessUtilityInvoiceUseCase(
        pdf_extractor=pdf_extractor,
        registry=registry,
        property_repo=property_repo,
        expense_repo=expense_repo,
        fallback_strategy=None,
    )


@pytest.fixture
def inbound_use_case(user_repo, utility_use_case):
    return ProcessInboundEmailUseCase(
        user_repo=user_repo,
        single_invoice_use_case=utility_use_case,
    )


def _create_user(user_repo, email="carlos@example.com", forwarding_email=None, user_id="user-carlos"):
    user = User(
        email=Email(email),
        password_hash=PasswordHash("$2b$12$dummyhashdummyhashdummyhashdummyhash"),
        username="carlos",
        forwarding_email=forwarding_email,
        id=user_id,
    )
    user_repo.save(user)
    return user


def _create_property(property_repo, user_id="user-carlos", cups=REPSOL_CUPS, prop_id="prop-1"):
    prop = Property(
        id=prop_id,
        name="Piso Centro",
        address=Address("Calle Mayor 1", "Madrid", "28013", "ES"),
        property_type=PropertyType.APARTMENT,
        user_id=user_id,
        status=PropertyStatus.RENTED,
        cups_electricity=cups,
    )
    property_repo.save(prop)
    return prop


def test_t_f21_uc_01_authorized_sender_main_email_creates_expense(
    inbound_use_case, user_repo, property_repo, expense_repo, sample_pdf_bytes
):
    """T-F21-UC-01: Remitente autorizado por email principal procesa PDF y crea gasto verificado."""
    user = _create_user(user_repo, email="carlos@example.com")
    prop = _create_property(property_repo, user_id=user.id)

    result = inbound_use_case.execute(
        sender="carlos@example.com",
        recipient="facturas@rental-handler.com",
        subject="Factura luz",
        attachments=[("factura_repsol.pdf", sample_pdf_bytes)],
    )

    assert result.status == "success"
    assert result.processed_count == 1
    assert result.duplicate_count == 0
    assert result.error_count == 0
    assert len(result.items) == 1

    item = result.items[0]
    assert item.status == "success"
    assert item.property_name == "Piso Centro"
    assert item.amount == Decimal("75.46")
    assert item.cups == REPSOL_CUPS

    # Verificar persistencia en ExpenseRepository
    expenses = expense_repo.find_by_property_id(prop.id)
    assert len(expenses) == 1
    exp = expenses[0]
    assert exp.amount.amount == Decimal("75.46")
    assert exp.is_verified is True
    assert exp.source == ExpenseSource.AUTO_IMPORT
    assert exp.category == ExpenseCategory.UTILITY
    assert exp.fiscal_category == FiscalExpenseCategory.SERVICIOS_SUMINISTROS


def test_t_f21_uc_02_authorized_sender_forwarding_email(
    inbound_use_case, user_repo, property_repo, expense_repo, sample_pdf_bytes
):
    """T-F21-UC-02: Remitente autorizado por forwarding_email procesa PDF correctamente."""
    user = _create_user(
        user_repo,
        email="carlos.login@corporate.com",
        forwarding_email="carlos.personal@gmail.com",
    )
    _create_property(property_repo, user_id=user.id)

    # El remitente es su correo alternativo
    result = inbound_use_case.execute(
        sender="carlos.personal@gmail.com",
        recipient="facturas@rental-handler.com",
        subject="Reenvío factura",
        attachments=[("factura_repsol.pdf", sample_pdf_bytes)],
    )

    assert result.status == "success"
    assert result.processed_count == 1
    assert result.items[0].status == "success"


def test_t_f21_uc_03_unauthorized_sender_rejected(
    inbound_use_case, user_repo, property_repo, expense_repo, sample_pdf_bytes
):
    """T-F21-UC-03: Remitente desconocido/no registrado es rechazado inmediatamente."""
    # Hay un usuario en la BD, pero el correo viene de otro remitente
    user = _create_user(user_repo, email="carlos@example.com")
    _create_property(property_repo, user_id=user.id)

    result = inbound_use_case.execute(
        sender="attacker@malicious.com",
        recipient="facturas@rental-handler.com",
        subject="Intento de inyección",
        attachments=[("factura.pdf", sample_pdf_bytes)],
    )

    assert result.status == "unauthorized_sender"
    assert result.processed_count == 0
    assert len(result.items) == 0
    assert "no está registrado ni autorizado" in result.message

    # Verificar que no se creó ningún gasto
    assert len(expense_repo.find_by_property_id("prop-1")) == 0


def test_t_f21_uc_04_anti_spoofing_cups_not_owned(
    inbound_use_case, user_repo, property_repo, expense_repo, sample_pdf_bytes
):
    """T-F21-UC-04: Remitente autorizado envía factura con CUPS que no le pertenece (aislamiento multi-tenant)."""
    # Usuario A (Víctima legítima dueña del CUPS)
    user_a = _create_user(user_repo, email="victima@example.com", user_id="user-victima")
    _create_property(property_repo, user_id=user_a.id, cups=REPSOL_CUPS, prop_id="prop-victima")

    # Usuario B (Remitente que intenta inyectar el gasto)
    user_b = _create_user(user_repo, email="intruso@example.com", user_id="user-intruso")
    _create_property(property_repo, user_id=user_b.id, cups="ES9999999999999999XX0F", prop_id="prop-intruso")

    result = inbound_use_case.execute(
        sender="intruso@example.com",
        recipient="facturas@rental-handler.com",
        subject="Factura de otra persona",
        attachments=[("factura.pdf", sample_pdf_bytes)],
    )

    assert result.status == "error"
    assert result.processed_count == 0
    assert result.error_count == 1
    assert len(result.items) == 1
    assert result.items[0].status == "cups_not_owned"

    # Ni la propiedad de la víctima ni la del intruso reciben ningún gasto
    assert len(expense_repo.find_by_property_id("prop-victima")) == 0
    assert len(expense_repo.find_by_property_id("prop-intruso")) == 0


def test_t_f21_uc_05_no_pdf_attachments_ignored(
    inbound_use_case, user_repo, property_repo
):
    """T-F21-UC-05: Correo sin adjuntos PDF es marcado como 'ignored'."""
    user = _create_user(user_repo, email="carlos@example.com")
    _create_property(property_repo, user_id=user.id)

    result = inbound_use_case.execute(
        sender="carlos@example.com",
        recipient="facturas@rental-handler.com",
        subject="Foto del contador",
        attachments=[("contador.jpg", b"\xff\xd8\xff...")],
    )

    assert result.status == "ignored"
    assert result.processed_count == 0
    assert len(result.items) == 0
    assert "No se encontraron archivos adjuntos PDF" in result.message


def test_t_f21_uc_06_duplicate_invoice_detected(
    inbound_use_case, user_repo, property_repo, sample_pdf_bytes
):
    """T-F21-UC-06: Factura ya existente es detectada y marcada como 'duplicate'."""
    user = _create_user(user_repo, email="carlos@example.com")
    _create_property(property_repo, user_id=user.id)

    # Primera ingesta: Éxito
    res1 = inbound_use_case.execute(
        sender="carlos@example.com",
        recipient="facturas@rental-handler.com",
        subject="Factura luz",
        attachments=[("factura.pdf", sample_pdf_bytes)],
    )
    assert res1.status == "success"
    assert res1.processed_count == 1

    # Segunda ingesta (mismo PDF): Duplicado
    res2 = inbound_use_case.execute(
        sender="carlos@example.com",
        recipient="facturas@rental-handler.com",
        subject="Factura luz reenviada otra vez",
        attachments=[("factura.pdf", sample_pdf_bytes)],
    )
    assert res2.status == "success"
    assert res2.processed_count == 0
    assert res2.duplicate_count == 1
    assert res2.items[0].status == "duplicate"


def test_t_f21_uc_07_rfc2822_sender_cleaning(
    inbound_use_case, user_repo, property_repo, sample_pdf_bytes
):
    """T-F21-UC-07: Remitente en formato RFC 2822 ('Carlos Cano <carlos@example.com>') se normaliza."""
    user = _create_user(user_repo, email="carlos@example.com")
    _create_property(property_repo, user_id=user.id)

    result = inbound_use_case.execute(
        sender='Carlos Cano <carlos@example.com>',
        recipient="facturas@rental-handler.com",
        subject="Factura",
        attachments=[("factura.pdf", sample_pdf_bytes)],
    )

    assert result.status == "success"
    assert result.sender == "carlos@example.com"
    assert result.processed_count == 1


def test_t_f21_uc_08_update_forwarding_email_use_case(user_repo):
    """T-F21-UC-08: UpdateForwardingEmailUseCase actualiza y valida email alternativo."""
    user = _create_user(user_repo, email="carlos@example.com")
    uc = UpdateForwardingEmailUseCase(user_repo)

    # Actualizar con email válido
    updated = uc.execute(user.id, "facturas.carlos@gmail.com")
    assert updated.forwarding_email == "facturas.carlos@gmail.com"

    # Buscar usuario por ese nuevo email de reenvío
    found = user_repo.find_by_sender_email("facturas.carlos@gmail.com")
    assert found is not None
    assert found.id == user.id

    # Limpiar / borrar forwarding_email
    cleared = uc.execute(user.id, None)
    assert cleared.forwarding_email is None

    # Error en sintaxis de email
    with pytest.raises(ValueError):
        uc.execute(user.id, "not-an-email")
