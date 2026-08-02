// src/types/index.ts

export interface Address {
  street: string;
  city: string;
  postal_code: string;
  country: string;
}

export interface Property {
  id: string;
  name: string;
  address: Address;
  property_type: string;
  status: string;
  image_url: string | null;
  has_fiscal_data?: boolean;
}

export interface Income {
  id: string;
  property_id: string;
  amount: string; // from backend Decimal
  currency: string;
  date: string;
  category: string;
  description: string;
  fiscal_category?: FiscalIncomeCategory | null;
}

export interface Expense {
  id: string;
  property_id: string;
  amount: string; // from backend Decimal
  currency: string;
  date: string;
  category: string;
  description: string;
  fiscal_category?: FiscalExpenseCategory | null;
}

export interface ProfitReport {
  property_id: string;
  net_profit: string; // from backend Decimal
  currency: string;
}

export interface PropertyCreateInput {
  name: string;
  address: Address;
  property_type: string;
}

export interface IncomeCreateInput {
  property_id: string;
  amount: number;
  date: string;
  category: string;
  description?: string;
  fiscal_category?: FiscalIncomeCategory | null;
}

export interface ExpenseCreateInput {
  property_id: string;
  amount: number;
  date: string;
  category: string;
  description?: string;
  fiscal_category?: FiscalExpenseCategory | null;
}

export interface UserResponse {
  id: string;
  email: string;
  username: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput {
  email: string;
  username: string;
  password: string;
}

export interface CadastralBreakdown {
  land_value: string;
  construction_value: string;
}

export interface AcquisitionCost {
  purchase_price: string;
  construction_portion: string;
  land_portion: string;
  transfer_tax: string;
  notary_fees: string;
  registry_fees: string;
}

export interface FiscalData {
  property_id: string;
  cadastral_ref: string | null;
  cadastral_breakdown: CadastralBreakdown | null;
  acquisition_cost: AcquisitionCost | null;
  acquisition_date: string | null;
  has_fiscal_data: boolean;
}

export interface FiscalDataInput {
  cadastral_ref?: string | null;
  cadastral_breakdown?: {
    land_value: number;
    construction_value: number;
  } | null;
  acquisition_cost?: {
    purchase_price: number;
    construction_portion: number;
    land_portion: number;
    transfer_tax?: number;
    notary_fees?: number;
    registry_fees?: number;
  } | null;
  acquisition_date?: string | null;
}

export interface LeaseContract {
  id: string;
  property_id: string;
  tenant_name: string;
  tenant_nif: string;
  start_date: string;
  end_date: string | null;
  monthly_rent: string;
  currency: string;
  lease_type: string;
  is_active: boolean;
}

export interface LeaseContractInput {
  tenant_name: string;
  tenant_nif: string;
  start_date: string;
  end_date?: string | null;
  monthly_rent: number;
  lease_type: string;
}

export type FiscalExpenseCategory =
  | "reparacion_conservacion"
  | "tributos_recargos"
  | "intereses_financiacion"
  | "amortizacion_inmueble"
  | "comunidad_propietarios"
  | "otros_gastos_deducibles"
  | "no_deducible";

export type FiscalIncomeCategory =
  | "rendimiento_integro"
  | "indemnizacion"
  | "otros_ingresos";

export interface FiscalSuggestionItem {
  id: string;
  category: string;
  suggested_fiscal_category: string;
  description: string;
  amount: string;
}

export interface FiscalSuggestionsResponse {
  unclassified_expenses: FiscalSuggestionItem[];
  unclassified_incomes: FiscalSuggestionItem[];
  total_unclassified: number;
}

export interface FiscalReport {
  fiscal_year: number;
  property_id: string;
  gross_rental_income: string;
  other_income: string;
  total_income: string;
  rented_days: number;
  total_days_in_year: number;
  occupation_ratio: string;
  expenses_intereses: string;
  expenses_reparacion: string;
  expenses_tributos: string;
  expenses_seguros: string;
  expenses_suministros: string;
  expenses_formalizacion: string;
  expenses_dudoso_cobro: string;
  expenses_otros: string;
  repair_interest_raw: string;
  repair_interest_cap: string;
  repair_interest_applied: string;
  repair_interest_excess: string;
  amortization_base: string;
  amortization_rate: string;
  amortization_full_year: string;
  amortization_prorated: string;
  total_deductible_expenses: string;
  net_income_before_reduction: string;
  vivienda_habitual_days: number;
  vivienda_habitual_ratio: string;
  reduction_base: string;
  reduction_percentage: string;
  reduction_amount: string;
  net_income_final: string;
  unclassified_income_count: number;
  unclassified_expense_count: number;
  has_warnings: boolean;
}
