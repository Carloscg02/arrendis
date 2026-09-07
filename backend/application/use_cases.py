"""
Casos de Uso (Application Layer).

Los casos de uso orquestan las operaciones de negocio. Reciben datos primitivos,
crean entidades y value objects internamente, y llaman a los repositorios (puertos).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from email.utils import parseaddr

from backend.domain.entities import (
    Expense,
    ExpenseCategory,
    ExpenseSource,
    FiscalExpenseCategory,
    Income,
    IncomeCategory,
    FiscalIncomeCategory,
    Property,
    PropertyStatus,
    PropertyType,
    User,
    LeaseContract,
    LeaseType,
    LLMProviderError,
    UtilityExtractionError,
    EmptyPDFTextError,
    ExtractionFailedError,
    PropertyNotFoundForCUPSError,
    DuplicateInvoiceError,
    InboundInvoiceItemResult,
    InboundEmailProcessResult,
)
from backend.domain.ports import (
    ExpenseRepository,
    IncomeRepository,
    PropertyRepository,
    UserRepository,
    PasswordHasherPort,
    TokenServicePort,
    LeaseContractRepository,
    FiscalReportRendererPort,
    FiscalCarryforwardRepository,
    LLMProviderPort,
    PDFTextExtractorPort,
)
from backend.domain.services import ProfitCalculator, FiscalCategoryMapper, FiscalCalculator
from backend.domain.value_objects import Address, Money, Email, PasswordHash, CadastralBreakdown, AcquisitionCost, FiscalReport, LLMRequest, UtilityInvoiceData
from backend.domain.extraction import ExtractionStrategy, UtilityExtractorRegistry

class CreatePropertyUseCase:
    """Caso de uso: crear y persistir una nueva propiedad."""

    def __init__(self, property_repo: PropertyRepository) -> None:
        self._property_repo = property_repo

    def execute(
        self,
        user_id: str,
        name: str,
        street: str,
        city: str,
        postal_code: str,
        country: str,
        property_type: str,
    ) -> Property:
        """Crea una Property con los datos proporcionados y la persiste.

        Args:
            name: Nombre descriptivo de la propiedad.
            street: Calle de la dirección.
            city: Ciudad.
            postal_code: Código postal.
            country: País (por defecto "ES").
            property_type: Tipo de propiedad (valor del enum PropertyType).

        Returns:
            La Property creada.
        """
        # Crear value objects
        address = Address(
            street=street,
            city=city,
            postal_code=postal_code,
            country=country,
        )

        # Regla de negocio: No permitir propiedades duplicadas por nombre
        existing_prop = self._property_repo.find_by_name(name)
        if existing_prop is not None:
            raise ValueError(f"Property with name '{name}' already exists.")

        # Crear la entidad
        prop = Property(
            name=name,
            address=address,
            property_type=PropertyType(property_type),
            user_id=user_id,
            status=PropertyStatus.AVAILABLE,
        )

        # Persistir
        self._property_repo.save(prop)

        return prop


class ListPropertiesUseCase:
    """Caso de uso: devolver todas las propiedades."""

    def __init__(self, property_repo: PropertyRepository) -> None:
        self._property_repo = property_repo

    def execute(self, user_id: str) -> list[Property]:
        """Retorna todas las propiedades registradas del usuario."""
        return self._property_repo.list_properties(user_id)

class GetPropertyUseCase:
    """Caso de uso: obtener una propiedad por su ID, validando que pertenezca al usuario."""
    def __init__(self, property_repo: PropertyRepository) -> None:
        self._property_repo = property_repo

    def execute(self, property_id: str, user_id: str) -> Property:
        prop = self._property_repo.find_by_id(property_id)
        if prop is None or prop.user_id != user_id:
            raise ValueError(f"No existe la propiedad con id '{property_id}'.")
        return prop


class RecordIncomeUseCase:
    """Caso de uso: registrar un ingreso vinculado a una propiedad."""

    def __init__(
        self,
        property_repo: PropertyRepository,
        income_repo: IncomeRepository,
    ) -> None:
        self._property_repo = property_repo
        self._income_repo = income_repo

    def execute(
        self,
        user_id: str,
        property_id: str,
        amount: Decimal,
        income_date: date,
        category: str,
        description: str = "",
        fiscal_category: str | None = None,
    ) -> Income:
        """Registra un ingreso para una propiedad existente."""
        # Validar que la propiedad exista y pertenezca al usuario
        prop = self._property_repo.find_by_id(property_id)
        if prop is None or prop.user_id != user_id:
            raise ValueError(
                f"No existe la propiedad con id '{property_id}'."
            )

        # Crear la entidad
        income = Income(
            property_id=property_id,
            amount=Money(amount, "EUR"),
            date=income_date,
            category=IncomeCategory(category),
            description=description,
            fiscal_category=FiscalIncomeCategory(fiscal_category) if fiscal_category else None,
        )

        # Persistir
        self._income_repo.save(income)

        return income


class RecordExpenseUseCase:
    """Caso de uso: registrar un gasto vinculado a una propiedad."""

    def __init__(
        self,
        property_repo: PropertyRepository,
        expense_repo: ExpenseRepository,
    ) -> None:
        self._property_repo = property_repo
        self._expense_repo = expense_repo

    def execute(
        self,
        user_id: str,
        property_id: str,
        amount: Decimal,
        expense_date: date,
        category: str,
        description: str = "",
        fiscal_category: str | None = None,
    ) -> Expense:
        """Registra un gasto para una propiedad existente."""
        # Validar que la propiedad exista y pertenezca al usuario
        prop = self._property_repo.find_by_id(property_id)
        if prop is None or prop.user_id != user_id:
            raise ValueError(
                f"No existe la propiedad con id '{property_id}'."
            )

        # Crear la entidad
        expense = Expense(
            property_id=property_id,
            amount=Money(amount, "EUR"),
            date=expense_date,
            category=ExpenseCategory(category),
            description=description,
            fiscal_category=FiscalExpenseCategory(fiscal_category) if fiscal_category else None,
        )

        # Persistir
        self._expense_repo.save(expense)

        return expense


class GetPropertyProfitReportUseCase:
    """Caso de uso: calcular el beneficio neto de una propiedad."""

    def __init__(
        self,
        property_repo: PropertyRepository,
        income_repo: IncomeRepository,
        expense_repo: ExpenseRepository,
    ) -> None:
        self._property_repo = property_repo
        self._income_repo = income_repo
        self._expense_repo = expense_repo

    def execute(self, user_id: str, property_id: str) -> Money:
        """Calcula el Net Profit de una propiedad.

        Args:
            property_id: ID de la propiedad.

        Returns:
            Money con el beneficio neto (puede ser negativo).

        Raises:
            ValueError: Si la propiedad no existe.
        """
        # Validar que la propiedad exista y pertenezca al usuario
        prop = self._property_repo.find_by_id(property_id)
        if prop is None or prop.user_id != user_id:
            raise ValueError(
                f"No existe la propiedad con id '{property_id}'."
            )

        # Obtener ingresos y gastos
        incomes = self._income_repo.find_by_property_id(property_id)
        expenses = self._expense_repo.find_by_property_id(property_id)

        # Delegar el cálculo al servicio de dominio
        return ProfitCalculator.calculate_net_profit(incomes, expenses)


class RegisterUserUseCase:
    def __init__(self, user_repo: UserRepository, hasher: PasswordHasherPort) -> None:
        self._user_repo = user_repo
        self._hasher = hasher

    def execute(self, email: str, username: str, password: str) -> User:
        # Check email not already registered
        existing = self._user_repo.find_by_email(email.strip().lower())
        if existing is not None:
            raise ValueError("Ya existe un usuario con ese email.")
        # Hash the password
        hashed = self._hasher.hash(password)
        # Create entity
        user = User(
            email=Email(email),
            password_hash=PasswordHash(hashed),
            username=username,
        )
        self._user_repo.save(user)
        return user


class LoginUserUseCase:
    def __init__(self, user_repo: UserRepository, hasher: PasswordHasherPort, tokens: TokenServicePort) -> None:
        self._user_repo = user_repo
        self._hasher = hasher
        self._tokens = tokens

    def execute(self, email: str, password: str) -> tuple[User, str, str]:
        user = self._user_repo.find_by_email(email.strip().lower())
        if user is None:
            raise ValueError("Credenciales incorrectas.")
        if not self._hasher.verify(password, user.password_hash.hash_value):
            raise ValueError("Credenciales incorrectas.")
        access = self._tokens.create_access_token(user.id)
        refresh = self._tokens.create_refresh_token(user.id)
        return user, access, refresh


class RefreshTokenUseCase:
    def __init__(self, user_repo: UserRepository, tokens: TokenServicePort) -> None:
        self._user_repo = user_repo
        self._tokens = tokens

    def execute(self, refresh_token: str) -> tuple[str, str]:
        user_id = self._tokens.verify_token(refresh_token)
        if user_id is None:
            raise ValueError("Token de refresco inválido o expirado.")
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            raise ValueError("Usuario no encontrado.")
        new_access = self._tokens.create_access_token(user.id)
        new_refresh = self._tokens.create_refresh_token(user.id)
        return new_access, new_refresh


class GetCurrentUserUseCase:
    def __init__(self, user_repo: UserRepository, tokens: TokenServicePort) -> None:
        self._user_repo = user_repo
        self._tokens = tokens

    def execute(self, access_token: str) -> User:
        user_id = self._tokens.verify_token(access_token)
        if user_id is None:
            raise ValueError("Token de acceso inválido o expirado.")
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            raise ValueError("Usuario no encontrado.")
        return user


class UpdatePropertyFiscalDataUseCase:
    """Caso de uso: actualizar los datos fiscales de una propiedad."""

    def __init__(self, property_repo: PropertyRepository) -> None:
        self._property_repo = property_repo

    def execute(
        self,
        user_id: str,
        property_id: str,
        cadastral_ref: str | None,
        land_value: Decimal | None,
        construction_value: Decimal | None,
        purchase_price: Decimal | None,
        construction_portion: Decimal | None,
        land_portion: Decimal | None,
        transfer_tax: Decimal | None,
        notary_fees: Decimal | None,
        registry_fees: Decimal | None,
        acquisition_date: date | None,
    ) -> Property:
        """Actualiza los datos fiscales de una propiedad existente."""
        prop = self._property_repo.find_by_id(property_id)
        if prop is None or prop.user_id != user_id:
            raise ValueError(f"No existe la propiedad con id '{property_id}'.")

        # Validate cadastral_ref length if provided before persisting
        if cadastral_ref is not None:
            ref_clean = cadastral_ref.strip()
            if not ref_clean:
                cadastral_ref = None
            elif len(ref_clean) != 20:
                raise ValueError(
                    f"La referencia catastral debe tener 20 caracteres, tiene {len(ref_clean)}."
                )
            else:
                cadastral_ref = ref_clean

        cadastral_breakdown: CadastralBreakdown | None = None
        if land_value is not None and construction_value is not None:
            cadastral_breakdown = CadastralBreakdown(
                land_value=land_value,
                construction_value=construction_value,
            )

        acquisition_cost: AcquisitionCost | None = None
        if purchase_price is not None:
            acquisition_cost = AcquisitionCost(
                purchase_price=purchase_price,
                construction_portion=construction_portion or Decimal("0"),
                land_portion=land_portion or Decimal("0"),
                transfer_tax=transfer_tax or Decimal("0"),
                notary_fees=notary_fees or Decimal("0"),
                registry_fees=registry_fees or Decimal("0"),
            )

        self._property_repo.update_fiscal_data(
            property_id=property_id,
            cadastral_ref=cadastral_ref,
            cadastral_breakdown=cadastral_breakdown,
            acquisition_cost=acquisition_cost,
            acquisition_date=acquisition_date,
        )

        updated = self._property_repo.find_by_id(property_id)
        assert updated is not None
        return updated


class GetPropertyFiscalDataUseCase:
    """Caso de uso: obtener los datos fiscales de una propiedad."""

    def __init__(self, property_repo: PropertyRepository) -> None:
        self._property_repo = property_repo

    def execute(self, user_id: str, property_id: str) -> Property:
        """Retorna la propiedad con sus datos fiscales."""
        prop = self._property_repo.find_by_id(property_id)
        if prop is None or prop.user_id != user_id:
            raise ValueError(f"No existe la propiedad con id '{property_id}'.")
        return prop


class CreateLeaseContractUseCase:
    def __init__(self, property_repo: PropertyRepository, contract_repo: LeaseContractRepository) -> None:
        self._property_repo = property_repo
        self._contract_repo = contract_repo

    def execute(
        self, user_id: str, property_id: str, tenant_name: str, tenant_nif: str,
        start_date: date, monthly_rent: Decimal, lease_type: str,
        end_date: date | None = None,
    ) -> LeaseContract:
        prop = self._property_repo.find_by_id(property_id)
        if prop is None or prop.user_id != user_id:
            raise ValueError(f"No existe la propiedad con id '{property_id}'.")

        contract = LeaseContract(
            property_id=property_id,
            tenant_name=tenant_name,
            tenant_nif=tenant_nif,
            start_date=start_date,
            end_date=end_date,
            monthly_rent=Money(monthly_rent, "EUR"),
            lease_type=LeaseType(lease_type),
        )
        self._contract_repo.save(contract)
        return contract

class ListLeaseContractsUseCase:
    def __init__(self, property_repo: PropertyRepository, contract_repo: LeaseContractRepository) -> None:
        self._property_repo = property_repo
        self._contract_repo = contract_repo

    def execute(self, user_id: str, property_id: str) -> list[LeaseContract]:
        prop = self._property_repo.find_by_id(property_id)
        if prop is None or prop.user_id != user_id:
            raise ValueError(f"No existe la propiedad con id '{property_id}'.")
        return self._contract_repo.find_by_property_id(property_id)


class UpdateLeaseContractUseCase:
    def __init__(self, property_repo: PropertyRepository, contract_repo: LeaseContractRepository) -> None:
        self._property_repo = property_repo
        self._contract_repo = contract_repo

    def execute(
        self, user_id: str, contract_id: str,
        tenant_name: str | None = None,
        tenant_nif: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        monthly_rent: Decimal | None = None,
        lease_type: str | None = None
    ) -> LeaseContract:
        contract = self._contract_repo.find_by_id(contract_id)
        if contract is None:
            raise ValueError(f"No existe el contrato con id '{contract_id}'.")

        prop = self._property_repo.find_by_id(contract.property_id)
        if prop is None or prop.user_id != user_id:
            raise ValueError("La propiedad del contrato no pertenece al usuario.")

        if tenant_name is not None:
            contract.tenant_name = tenant_name
        if tenant_nif is not None:
            contract.tenant_nif = tenant_nif
        if start_date is not None:
            contract.start_date = start_date
        if end_date is not None:
            contract.end_date = end_date
        if monthly_rent is not None:
            contract.monthly_rent = Money(monthly_rent, "EUR")
        if lease_type is not None:
            contract.lease_type = LeaseType(lease_type)

        contract.__post_init__()
        self._contract_repo.save(contract)
        return contract


class DeleteLeaseContractUseCase:
    def __init__(self, property_repo: PropertyRepository, contract_repo: LeaseContractRepository) -> None:
        self._property_repo = property_repo
        self._contract_repo = contract_repo

    def execute(self, user_id: str, contract_id: str) -> None:
        contract = self._contract_repo.find_by_id(contract_id)
        if contract is None:
            raise ValueError(f"No existe el contrato con id '{contract_id}'.")
        prop = self._property_repo.find_by_id(contract.property_id)
        if prop is None or prop.user_id != user_id:
            raise ValueError("La propiedad del contrato no pertenece al usuario.")
        self._contract_repo.delete(contract_id)


class UpdateFiscalCategoryUseCase:
    def __init__(self, property_repo: PropertyRepository, income_repo: IncomeRepository, expense_repo: ExpenseRepository):
        self._property_repo = property_repo
        self._income_repo = income_repo
        self._expense_repo = expense_repo

    def execute(self, user_id: str, record_id: str, record_type: str, fiscal_category: str) -> Income | Expense:
        if record_type not in ("income", "expense"):
            raise ValueError("record_type must be 'income' or 'expense'")

        record = None
        props = self._property_repo.list_properties(user_id)
        prop_ids = {p.id for p in props}
        
        if record_type == "income":
            for pid in prop_ids:
                for inc in self._income_repo.find_by_property_id(pid):
                    if inc.id == record_id:
                        record = inc
                        break
                if record: break
        else:
            for pid in prop_ids:
                for exp in self._expense_repo.find_by_property_id(pid):
                    if exp.id == record_id:
                        record = exp
                        break
                if record: break

        if not record:
            raise ValueError("Registro no encontrado o no pertenece al usuario.")

        if record_type == "income":
            try:
                _ = FiscalIncomeCategory(fiscal_category)
            except ValueError:
                raise ValueError("Categoría fiscal inválida.")
            self._income_repo.update_fiscal_category(record_id, fiscal_category)
            record.fiscal_category = FiscalIncomeCategory(fiscal_category)
            return record
        else:
            try:
                _ = FiscalExpenseCategory(fiscal_category)
            except ValueError:
                raise ValueError("Categoría fiscal inválida.")
            self._expense_repo.update_fiscal_category(record_id, fiscal_category)
            record.fiscal_category = FiscalExpenseCategory(fiscal_category)
            return record

class SuggestFiscalCategoriesUseCase:
    def __init__(self, property_repo: PropertyRepository, income_repo: IncomeRepository, expense_repo: ExpenseRepository):
        self._property_repo = property_repo
        self._income_repo = income_repo
        self._expense_repo = expense_repo

    def execute(self, user_id: str, property_id: str) -> dict:
        prop = self._property_repo.find_by_id(property_id)
        if prop is None or prop.user_id != user_id:
            raise ValueError("No existe la propiedad o no pertenece al usuario.")

        incomes = self._income_repo.find_by_property_id(property_id)
        expenses = self._expense_repo.find_by_property_id(property_id)

        unclassified_incomes = []
        for i in incomes:
            if i.fiscal_category is None:
                suggested = FiscalCategoryMapper.suggest_income_fiscal_category(i.category)
                unclassified_incomes.append({
                    "id": i.id,
                    "category": i.category.value,
                    "suggested_fiscal_category": suggested.value,
                    "description": i.description,
                    "amount": i.amount.amount,
                    "date": i.date,
                })

        unclassified_expenses = []
        for e in expenses:
            if e.fiscal_category is None:
                suggested = FiscalCategoryMapper.suggest_expense_fiscal_category(e.category)
                unclassified_expenses.append({
                    "id": e.id,
                    "category": e.category.value,
                    "suggested_fiscal_category": suggested.value,
                    "description": e.description,
                    "amount": e.amount.amount,
                    "date": e.date,
                })

        return {
            "unclassified_expenses": unclassified_expenses,
            "unclassified_incomes": unclassified_incomes,
            "total_unclassified": len(unclassified_expenses) + len(unclassified_incomes)
        }


class GenerateFiscalReportUseCase:
    """Caso de uso: generar el informe fiscal para una propiedad y año."""

    def __init__(
        self,
        property_repo: PropertyRepository,
        income_repo: IncomeRepository,
        expense_repo: ExpenseRepository,
        contract_repo: LeaseContractRepository,
        carryforward_repo: FiscalCarryforwardRepository | None = None,
    ) -> None:
        self._property_repo = property_repo
        self._income_repo = income_repo
        self._expense_repo = expense_repo
        self._contract_repo = contract_repo
        self._carryforward_repo = carryforward_repo

    def execute(self, user_id: str, property_id: str, fiscal_year: int) -> FiscalReport:
        prop = self._property_repo.find_by_id(property_id)
        if prop is None or prop.user_id != user_id:
            raise ValueError(f"No existe la propiedad con id '{property_id}'.")
        if not prop.has_fiscal_data:
            raise ValueError("La propiedad no tiene datos fiscales completos.")

        incomes = self._income_repo.find_by_property_id(property_id)
        expenses = self._expense_repo.find_by_property_id(property_id)
        contracts = self._contract_repo.find_by_property_id(property_id)
        carryforwards = (
            self._carryforward_repo.find_available_for_year(property_id, fiscal_year)
            if self._carryforward_repo else []
        )

        return FiscalCalculator.calculate(
            fiscal_year=fiscal_year,
            property=prop,
            incomes=incomes,
            expenses=expenses,
            contracts=contracts,
            prior_carryforwards=carryforwards,
        )


class DownloadFiscalReportPdfUseCase:
    """Caso de uso: generar el informe fiscal en PDF descargable."""

    def __init__(
        self,
        property_repo: PropertyRepository,
        income_repo: IncomeRepository,
        expense_repo: ExpenseRepository,
        contract_repo: LeaseContractRepository,
        renderer: FiscalReportRendererPort,
        carryforward_repo: FiscalCarryforwardRepository | None = None,
    ) -> None:
        self._property_repo = property_repo
        self._income_repo = income_repo
        self._expense_repo = expense_repo
        self._contract_repo = contract_repo
        self._renderer = renderer
        self._carryforward_repo = carryforward_repo

    def execute(self, user_id: str, property_id: str, fiscal_year: int) -> tuple[bytes, str, str]:
        """Genera el PDF del borrador fiscal.

        Returns:
            Tupla (pdf_bytes, content_type, filename).
        """
        # 1. Obtener property y validar
        prop = self._property_repo.find_by_id(property_id)
        if prop is None or prop.user_id != user_id:
            raise ValueError(f"No existe la propiedad con id '{property_id}'.")
        if not prop.has_fiscal_data:
            raise ValueError("La propiedad no tiene datos fiscales completos.")

        # 2. Recopilar datos
        incomes = self._income_repo.find_by_property_id(property_id)
        expenses = self._expense_repo.find_by_property_id(property_id)
        contracts = self._contract_repo.find_by_property_id(property_id)
        carryforwards = (
            self._carryforward_repo.find_available_for_year(property_id, fiscal_year)
            if self._carryforward_repo else []
        )

        # 3. Calcular el FiscalReport
        report = FiscalCalculator.calculate(
            fiscal_year=fiscal_year,
            property=prop,
            incomes=incomes,
            expenses=expenses,
            contracts=contracts,
            prior_carryforwards=carryforwards,
        )

        # 4. Renderizar a PDF
        address_str = str(prop.address) if prop.address else ""
        pdf_bytes = self._renderer.render(report, prop.name, address_str)

        # 5. Construir filename
        safe_name = prop.name.replace(" ", "_").replace("/", "_")
        filename = f"borrador_fiscal_{safe_name}_{fiscal_year}.{self._renderer.file_extension()}"

        return pdf_bytes, self._renderer.content_type(), filename


class CheckLLMHealthUseCase:
    """Verifica la disponibilidad del proveedor de LLM."""
    
    def __init__(self, llm_provider: LLMProviderPort | None):
        self._llm = llm_provider
    
    def execute(self) -> dict:
        if self._llm is None:
            return {"status": "not_configured", "model": None}
        # Intenta una generación trivial para verificar conectividad
        try:
            response = self._llm.generate(LLMRequest(user_prompt="ping"))
            return {"status": "ok", "model": response.model_name}
        except LLMProviderError as e:
            return {"status": "error", "model": None, "message": str(e)}


@dataclass(frozen=True)
class ProcessUtilityInvoiceResult:
    """DTO de resultado de la ingesta y extracción de una factura de suministros."""
    expense: Expense
    property: Property
    invoice_data: UtilityInvoiceData
    strategy_used: str


class ProcessUtilityInvoiceUseCase:
    """Caso de uso: procesar una factura PDF, extraer sus datos y registrar el gasto directamente verificado."""

    def __init__(
        self,
        pdf_extractor: PDFTextExtractorPort,
        registry: UtilityExtractorRegistry,
        property_repo: PropertyRepository,
        expense_repo: ExpenseRepository,
        fallback_strategy: ExtractionStrategy | None = None,
    ) -> None:
        self._pdf_extractor = pdf_extractor
        self._registry = registry
        self._property_repo = property_repo
        self._expense_repo = expense_repo
        self._fallback_strategy = fallback_strategy

    def execute(self, pdf_bytes: bytes, user_id: str) -> ProcessUtilityInvoiceResult:
        """Procesa una factura PDF y crea un Expense verificado.

        Args:
            pdf_bytes: Bytes del archivo PDF de la factura.
            user_id: ID del usuario autenticado (para matching multi-tenant).

        Returns:
            ProcessUtilityInvoiceResult con el gasto creado y metadatos.

        Raises:
            EmptyPDFTextError: Si el PDF no contiene texto digital extraíble.
            ExtractionFailedError: Si ni Regex ni IA lograron extraer los datos requeridos.
            PropertyNotFoundForCUPSError: Si el CUPS extraído no pertenece a ninguna propiedad del usuario.
            DuplicateInvoiceError: Si la factura ya fue importada previamente para la propiedad.
        """
        # 1. Extraer texto plano con PyMuPDF
        raw_text = self._pdf_extractor.extract_text(pdf_bytes)

        # 2. Intentar estrategia Regex según comercializadora
        invoice_data: UtilityInvoiceData | None = None
        strategy_used = "unknown"
        strategy = self._registry.find_strategy(raw_text)

        if strategy is not None:
            invoice_data = strategy.extract(raw_text)
            if invoice_data is not None:
                strategy_used = strategy.provider_name

        # 3. Fallback a IA si no hubo coincidencia Regex o falló la extracción
        if invoice_data is None:
            if self._fallback_strategy is None:
                raise ExtractionFailedError(
                    "No se pudo extraer la factura con reglas Regex y no hay estrategia de IA configurada."
                )
            invoice_data = self._fallback_strategy.extract(raw_text)
            if invoice_data is None:
                raise ExtractionFailedError(
                    "La extracción de la factura no pudo completarse ni por Regex ni por IA."
                )
            strategy_used = self._fallback_strategy.provider_name

        # 4. Matching unívoco CUPS -> Property del usuario
        prop = self._property_repo.find_by_cups(invoice_data.cups, user_id=user_id)
        if prop is None:
            raise PropertyNotFoundForCUPSError(
                f"No se encontró ningún inmueble del usuario con el CUPS '{invoice_data.cups}'.",
                cups=invoice_data.cups,
                invoice_data=invoice_data,
            )

        # 5. Detección de duplicados (Idempotencia)
        existing_expenses = self._expense_repo.find_by_property_id(prop.id)
        for exp in existing_expenses:
            if exp.utility_data is not None and exp.utility_data.cups == invoice_data.cups:
                # Criterio 1: Mismo número de factura
                if invoice_data.invoice_number and exp.utility_data.invoice_number == invoice_data.invoice_number:
                    raise DuplicateInvoiceError(
                        f"La factura de {invoice_data.provider_name} con nº {invoice_data.invoice_number} ya fue importada previamente.",
                        existing_expense=exp,
                        invoice_data=invoice_data,
                    )
                # Criterio 2: Misma fecha y mismo importe
                if exp.date == invoice_data.issue_date and exp.amount.amount == invoice_data.amount:
                    raise DuplicateInvoiceError(
                        f"Ya existe una factura de {invoice_data.provider_name} del {invoice_data.issue_date} por importe de {invoice_data.amount} €.",
                        existing_expense=exp,
                        invoice_data=invoice_data,
                    )

        # 6. Crear Expense directamente verificado (AUTO_IMPORT)
        expense = Expense(
            property_id=prop.id,
            amount=Money(invoice_data.amount, "EUR"),
            date=invoice_data.issue_date,
            category=ExpenseCategory.UTILITY,
            description=f"Factura {invoice_data.provider_name} - {invoice_data.invoice_number or invoice_data.cups}",
            fiscal_category=FiscalExpenseCategory.SERVICIOS_SUMINISTROS,
            is_verified=True,
            source=ExpenseSource.AUTO_IMPORT,
            utility_data=invoice_data,
        )

        # 7. Persistir el gasto
        self._expense_repo.save(expense)

        return ProcessUtilityInvoiceResult(
            expense=expense,
            property=prop,
            invoice_data=invoice_data,
            strategy_used=strategy_used,
        )


@dataclass(frozen=True)
class BatchInvoiceUploadItem:
    """Resultado individual dentro de un lote de subida de facturas."""
    filename: str
    status: str  # "success" | "duplicate" | "error"
    expense: Expense | None = None
    property_name: str | None = None
    message: str | None = None
    cups: str | None = None
    amount: Decimal | None = None


@dataclass(frozen=True)
class BatchInvoiceUploadResult:
    """Resumen consolidado del procesamiento de un lote de facturas."""
    total_processed: int
    successful_count: int
    duplicate_count: int
    error_count: int
    total_amount_imported: Decimal
    items: list[BatchInvoiceUploadItem]


class ProcessBatchUtilityInvoicesUseCase:
    """Caso de uso: procesar múltiples facturas PDF en lote."""

    def __init__(self, single_invoice_use_case: ProcessUtilityInvoiceUseCase) -> None:
        self._single_use_case = single_invoice_use_case

    def execute(
        self, files: list[tuple[str, bytes]], user_id: str
    ) -> BatchInvoiceUploadResult:
        items: list[BatchInvoiceUploadItem] = []
        successful_count = 0
        duplicate_count = 0
        error_count = 0
        total_amount = Decimal("0")

        for filename, pdf_bytes in files:
            try:
                res = self._single_use_case.execute(pdf_bytes, user_id)
                items.append(
                    BatchInvoiceUploadItem(
                        filename=filename,
                        status="success",
                        expense=res.expense,
                        property_name=res.property.name,
                        amount=res.invoice_data.amount,
                        cups=res.invoice_data.cups,
                    )
                )
                successful_count += 1
                total_amount += res.invoice_data.amount
            except DuplicateInvoiceError as e:
                duplicate_count += 1
                cups_val = getattr(e, 'cups', None) or (e.invoice_data.cups if getattr(e, 'invoice_data', None) else None)
                items.append(
                    BatchInvoiceUploadItem(
                        filename=filename,
                        status="duplicate",
                        message=str(e),
                        cups=cups_val,
                    )
                )
            except Exception as e:
                error_count += 1
                items.append(
                    BatchInvoiceUploadItem(
                        filename=filename,
                        status="error",
                        message=str(e),
                    )
                )

        return BatchInvoiceUploadResult(
            total_processed=len(files),
            successful_count=successful_count,
            duplicate_count=duplicate_count,
            error_count=error_count,
            total_amount_imported=total_amount,
            items=items,
        )


class UpdateForwardingEmailUseCase:
    """Caso de uso: actualizar el email de reenvío autorizado para la ingesta de facturas."""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def execute(self, user_id: str, forwarding_email: str | None) -> User:
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            raise ValueError(f"No existe el usuario con id '{user_id}'.")

        clean = forwarding_email.strip().lower() if forwarding_email and forwarding_email.strip() else None
        if clean:
            # Validar sintaxis con el Value Object Email
            Email(clean)

        self._user_repo.update_forwarding_email(user_id, clean)
        user.forwarding_email = clean
        return user


class ProcessInboundEmailUseCase:
    """Caso de uso: Procesar facturas de suministros recibidas por email (F-21).

    Verifica la identidad del remitente contra los emails autorizados del usuario
    (email de registro o forwarding_email), filtra los adjuntos PDF, extrae los
    datos de la factura y persiste el gasto verificado si el CUPS pertenece a un
    inmueble del usuario.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        single_invoice_use_case: ProcessUtilityInvoiceUseCase,
    ) -> None:
        self._user_repo = user_repo
        self._single_use_case = single_invoice_use_case

    def execute(
        self,
        sender: str,
        recipient: str,
        subject: str,
        attachments: list[tuple[str, bytes]],
    ) -> InboundEmailProcessResult:
        # 1. Normalizar y extraer email del remitente (RFC 2822)
        _, sender_address = parseaddr(sender)
        clean_sender = sender_address.strip().lower()
        if not clean_sender and "@" in sender:
            import re
            m = re.search(r'[\w\.-]+@[\w\.-]+', sender)
            if m:
                clean_sender = m.group(0).lower()

        # 2. Anti-Spoofing: Verificar si el remitente corresponde a un usuario registrado o autorizado
        user = self._user_repo.find_by_sender_email(clean_sender)
        if user is None:
            return InboundEmailProcessResult(
                status="unauthorized_sender",
                sender=clean_sender or sender,
                recipient=recipient,
                subject=subject,
                total_attachments=len(attachments),
                processed_count=0,
                duplicate_count=0,
                error_count=0,
                items=[],
                message=f"El remitente '{clean_sender or sender}' no está registrado ni autorizado como dirección de reenvío.",
            )

        # 3. Filtrar únicamente adjuntos PDF
        pdf_attachments = [
            (filename, content)
            for filename, content in attachments
            if filename.lower().endswith(".pdf")
        ]

        if not pdf_attachments:
            return InboundEmailProcessResult(
                status="ignored",
                sender=clean_sender,
                recipient=recipient,
                subject=subject,
                total_attachments=len(attachments),
                processed_count=0,
                duplicate_count=0,
                error_count=0,
                items=[],
                message="No se encontraron archivos adjuntos PDF en el correo recibido.",
            )

        # 4. Procesar cada archivo PDF usando el user_id autenticado
        items: list[InboundInvoiceItemResult] = []
        processed_count = 0
        duplicate_count = 0
        error_count = 0

        for filename, pdf_bytes in pdf_attachments:
            try:
                res = self._single_use_case.execute(pdf_bytes, user.id)
                items.append(
                    InboundInvoiceItemResult(
                        filename=filename,
                        status="success",
                        expense=res.expense,
                        property_name=res.property.name,
                        amount=res.invoice_data.amount,
                        cups=res.invoice_data.cups,
                    )
                )
                processed_count += 1
            except DuplicateInvoiceError as e:
                duplicate_count += 1
                cups_val = getattr(e, 'cups', None) or (e.invoice_data.cups if getattr(e, 'invoice_data', None) else None)
                items.append(
                    InboundInvoiceItemResult(
                        filename=filename,
                        status="duplicate",
                        message=str(e),
                        cups=cups_val,
                    )
                )
            except PropertyNotFoundForCUPSError as e:
                error_count += 1
                items.append(
                    InboundInvoiceItemResult(
                        filename=filename,
                        status="cups_not_owned",
                        message=str(e),
                        cups=e.cups,
                    )
                )
            except Exception as e:
                error_count += 1
                items.append(
                    InboundInvoiceItemResult(
                        filename=filename,
                        status="error",
                        message=str(e),
                    )
                )

        if processed_count > 0 or duplicate_count > 0:
            status = "success"
            msg = f"Se procesaron {processed_count} facturas correctamente ({duplicate_count} duplicadas omitidas)."
        elif error_count > 0:
            status = "error"
            msg = "Ocurrieron errores al procesar los adjuntos del correo."
        else:
            status = "ignored"
            msg = "No se procesó ningún documento."

        return InboundEmailProcessResult(
            status=status,
            sender=clean_sender,
            recipient=recipient,
            subject=subject,
            total_attachments=len(attachments),
            processed_count=processed_count,
            duplicate_count=duplicate_count,
            error_count=error_count,
            items=items,
            message=msg,
        )



