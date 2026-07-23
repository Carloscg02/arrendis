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
}

export interface Income {
  id: string;
  property_id: string;
  amount: string; // from backend Decimal
  currency: string;
  date: string;
  category: string;
  description: string;
}

export interface Expense {
  id: string;
  property_id: string;
  amount: string; // from backend Decimal
  currency: string;
  date: string;
  category: string;
  description: string;
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
}

export interface ExpenseCreateInput {
  property_id: string;
  amount: number;
  date: string;
  category: string;
  description?: string;
}
