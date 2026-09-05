import pytest

from datetime import date
from backend.domain.entities import Expense, Income, Property, User, LeaseContract
from backend.domain.ports import ExpenseRepository, IncomeRepository, PropertyRepository, UserRepository, PasswordHasherPort, TokenServicePort, LeaseContractRepository
from backend.domain.value_objects import CadastralBreakdown, AcquisitionCost, LLMResponse
from backend.domain.ports import LLMProviderPort


class InMemoryPropertyRepository(PropertyRepository):
    """Implementación in-memory de PropertyRepository para tests unitarios."""

    def __init__(self) -> None:
        self._store: dict[str, Property] = {}

    def save(self, property: Property) -> None:
        self._store[property.id] = property

    def find_by_id(self, property_id: str) -> Property | None:
        return self._store.get(property_id)

    def find_by_name(self, name: str) -> Property | None:
        for p in self._store.values():
            if p.name == name:
                return p
        return None

    def list_properties(self, user_id: str) -> list[Property]:
        return [p for p in self._store.values() if p.user_id == user_id]

    def delete(self, property_id: str) -> None:
        self._store.pop(property_id, None)

    def update_image(self, property_id: str, image_filename: str | None) -> None:
        for prop in self._store.values():
            if prop.id == property_id:
                prop.image_filename = image_filename
                return

    def update_fiscal_data(
        self,
        property_id: str,
        cadastral_ref: str | None,
        cadastral_breakdown: CadastralBreakdown | None,
        acquisition_cost: AcquisitionCost | None,
        acquisition_date: date | None,
    ) -> None:
        prop = self._store.get(property_id)
        if prop:
            prop.cadastral_ref = cadastral_ref
            prop.cadastral_breakdown = cadastral_breakdown
            prop.acquisition_cost = acquisition_cost
            prop.acquisition_date = acquisition_date

    def find_by_cups(self, cups: str, user_id: str) -> Property | None:
        for p in self._store.values():
            if p.user_id == user_id and (
                p.cups_electricity == cups or p.cups_gas == cups or p.cups_water == cups
            ):
                return p
        return None

    def update_cups(
        self,
        property_id: str,
        cups_electricity: str | None,
        cups_gas: str | None,
        cups_water: str | None,
    ) -> None:
        prop = self._store.get(property_id)
        if prop:
            prop.cups_electricity = cups_electricity
            prop.cups_gas = cups_gas
            prop.cups_water = cups_water


class InMemoryIncomeRepository(IncomeRepository):
    """Implementación in-memory de IncomeRepository para tests unitarios."""

    def __init__(self) -> None:
        self._store: dict[str, Income] = {}

    def save(self, income: Income) -> None:
        self._store[income.id] = income

    def find_by_property_id(self, property_id: str) -> list[Income]:
        return [i for i in self._store.values() if i.property_id == property_id]

    def delete(self, income_id: str) -> None:
        self._store.pop(income_id, None)

    def update_fiscal_category(self, record_id: str, fiscal_category: str | None) -> None:
        from backend.domain.entities import FiscalIncomeCategory
        record = self._store.get(record_id)
        if record:
            record.fiscal_category = FiscalIncomeCategory(fiscal_category) if fiscal_category else None


class InMemoryExpenseRepository(ExpenseRepository):
    """Implementación in-memory de ExpenseRepository para tests unitarios."""

    def __init__(self) -> None:
        self._store: dict[str, Expense] = {}

    def save(self, expense: Expense) -> None:
        self._store[expense.id] = expense

    def find_by_property_id(self, property_id: str) -> list[Expense]:
        return [e for e in self._store.values() if e.property_id == property_id]

    def find_by_id(self, expense_id: str) -> Expense | None:
        return self._store.get(expense_id)

    def delete(self, expense_id: str) -> None:
        self._store.pop(expense_id, None)

    def update_fiscal_category(self, record_id: str, fiscal_category: str | None) -> None:
        from backend.domain.entities import FiscalExpenseCategory
        record = self._store.get(record_id)
        if record:
            record.fiscal_category = FiscalExpenseCategory(fiscal_category) if fiscal_category else None


@pytest.fixture
def property_repo() -> InMemoryPropertyRepository:
    """Retorna un repositorio de propiedades in-memory limpio."""
    return InMemoryPropertyRepository()


@pytest.fixture
def income_repo() -> InMemoryIncomeRepository:
    """Retorna un repositorio de ingresos in-memory limpio."""
    return InMemoryIncomeRepository()


@pytest.fixture
def expense_repo() -> InMemoryExpenseRepository:
    """Retorna un repositorio de gastos in-memory limpio."""
    return InMemoryExpenseRepository()


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._users: list[User] = []
    def save(self, user: User) -> None:
        self._users.append(user)
    def find_by_id(self, user_id: str) -> User | None:
        return next((u for u in self._users if u.id == user_id), None)
    def find_by_email(self, email: str) -> User | None:
        return next((u for u in self._users if u.email.value == email.lower()), None)

class FakePasswordHasherAdapter(PasswordHasherPort):
    """Hasher falso para tests: hash = '$2b$fake$' + password, verify = comparación directa."""
    def hash(self, plain_password: str) -> str:
        return f"$2b$fake${plain_password}"
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return hashed_password == f"$2b$fake${plain_password}"

class FakeTokenServiceAdapter(TokenServicePort):
    """Token service falso para tests: tokens son el user_id directamente."""
    def create_access_token(self, user_id: str) -> str:
        return f"access-{user_id}"
    def create_refresh_token(self, user_id: str) -> str:
        return f"refresh-{user_id}"
    def verify_token(self, token: str) -> str | None:
        for prefix in ("access-", "refresh-"):
            if token.startswith(prefix):
                return token[len(prefix):]
        return None

@pytest.fixture
def user_repo():
    return InMemoryUserRepository()

@pytest.fixture
def hasher():
    return FakePasswordHasherAdapter()

@pytest.fixture
def token_service():
    return FakeTokenServiceAdapter()

class InMemoryLeaseContractRepository(LeaseContractRepository):
    def __init__(self) -> None:
        self._store: dict[str, LeaseContract] = {}

    def save(self, contract: LeaseContract) -> None:
        self._store[contract.id] = contract

    def find_by_id(self, contract_id: str) -> LeaseContract | None:
        return self._store.get(contract_id)

    def find_by_property_id(self, property_id: str) -> list[LeaseContract]:
        return sorted(
            [c for c in self._store.values() if c.property_id == property_id],
            key=lambda c: c.start_date,
            reverse=True
        )

    def delete(self, contract_id: str) -> None:
        self._store.pop(contract_id, None)

@pytest.fixture
def lease_contract_repo() -> InMemoryLeaseContractRepository:
    return InMemoryLeaseContractRepository()

@pytest.fixture
def sqlite_connection():
    from backend.adapters.sqlite_adapter import SQLiteConnection
    conn = SQLiteConnection(db_path=":memory:")
    yield conn
    conn.close()


class FakeLLMProviderAdapter(LLMProviderPort):
    """LLM falso para tests: retorna un texto fijo."""
    def __init__(self, response_text: str = "fake response") -> None:
        self._response_text = response_text

    def generate(self, request) -> LLMResponse:
        return LLMResponse(
            text=self._response_text,
            model_name="fake-model",
            input_tokens=5,
            output_tokens=10,
        )


@pytest.fixture
def fake_llm():
    return FakeLLMProviderAdapter()

