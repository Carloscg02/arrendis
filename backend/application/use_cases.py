"""
Casos de Uso (Application Layer).

Los casos de uso orquestan las operaciones de negocio. Reciben datos primitivos,
crean entidades y value objects internamente, y llaman a los repositorios (puertos).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from backend.domain.entities import (
    Expense,
    ExpenseCategory,
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
)
from backend.domain.services import ProfitCalculator, FiscalCategoryMapper, FiscalCalculator
from backend.domain.value_objects import Address, Money, Email, PasswordHash, CadastralBreakdown, AcquisitionCost, FiscalReport

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
    ) -> None:
        self._property_repo = property_repo
        self._income_repo = income_repo
        self._expense_repo = expense_repo
        self._contract_repo = contract_repo

    def execute(self, user_id: str, property_id: str, fiscal_year: int) -> FiscalReport:
        prop = self._property_repo.find_by_id(property_id)
        if prop is None or prop.user_id != user_id:
            raise ValueError(f"No existe la propiedad con id '{property_id}'.")
        if not prop.has_fiscal_data:
            raise ValueError("La propiedad no tiene datos fiscales completos.")

        incomes = self._income_repo.find_by_property_id(property_id)
        expenses = self._expense_repo.find_by_property_id(property_id)
        contracts = self._contract_repo.find_by_property_id(property_id)

        return FiscalCalculator.calculate(
            fiscal_year=fiscal_year,
            property=prop,
            incomes=incomes,
            expenses=expenses,
            contracts=contracts,
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
    ) -> None:
        self._property_repo = property_repo
        self._income_repo = income_repo
        self._expense_repo = expense_repo
        self._contract_repo = contract_repo
        self._renderer = renderer

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

        # 3. Calcular el FiscalReport
        report = FiscalCalculator.calculate(
            fiscal_year=fiscal_year,
            property=prop,
            incomes=incomes,
            expenses=expenses,
            contracts=contracts,
        )

        # 4. Renderizar a PDF
        address_str = str(prop.address) if prop.address else ""
        pdf_bytes = self._renderer.render(report, prop.name, address_str)

        # 5. Construir filename
        safe_name = prop.name.replace(" ", "_").replace("/", "_")
        filename = f"borrador_fiscal_{safe_name}_{fiscal_year}.{self._renderer.file_extension()}"

        return pdf_bytes, self._renderer.content_type(), filename

