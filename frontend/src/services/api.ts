import type {
  Property,
  PropertyCreateInput,
  Income,
  IncomeCreateInput,
  Expense,
  ExpenseCreateInput,
  ProfitReport,
  FiscalData,
  FiscalDataInput,
  LeaseContract,
  LeaseContractInput,
} from "../types";
import * as authService from './auth';

const API_BASE = "http://localhost:8000/api";

async function apiFetch(url: string, options?: RequestInit): Promise<Response> {
  let token = authService.getAccessToken();
  const headers = new Headers(options?.headers || {});
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  let res = await fetch(url, { ...options, headers });
  
  if (res.status === 401) {
    try {
      await authService.refresh();
      token = authService.getAccessToken();
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      res = await fetch(url, { ...options, headers });
    } catch (e) {
      authService.clearSession();
      window.location.href = '/login';
    }
  }
  
  return res;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    try {
      const json = JSON.parse(text);
      throw new Error(json.detail || text);
    } catch {
      throw new Error(text);
    }
  }
  // Si no hay contenido (por ejemplo DELETE 204 o 200 sin body), devolvemos vacio
  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return {} as T;
  }
  return res.json();
}

export async function getProperties(): Promise<Property[]> {
  const res = await apiFetch(`${API_BASE}/properties`);
  return handleResponse<Property[]>(res);
}

export async function createProperty(data: PropertyCreateInput): Promise<Property> {
  const res = await apiFetch(`${API_BASE}/properties`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Property>(res);
}

export async function getPropertyById(id: string): Promise<Property> {
  const res = await apiFetch(`${API_BASE}/properties/${id}`);
  return handleResponse<Property>(res);
}

export async function deleteProperty(id: string): Promise<void> {
  const res = await apiFetch(`${API_BASE}/properties/${id}`, { method: "DELETE" });
  await handleResponse<void>(res);
}

export async function getIncomes(propertyId: string): Promise<Income[]> {
  const res = await apiFetch(`${API_BASE}/properties/${propertyId}/incomes`);
  return handleResponse<Income[]>(res);
}

export async function createIncome(data: IncomeCreateInput): Promise<Income> {
  const res = await apiFetch(`${API_BASE}/incomes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Income>(res);
}

export async function getExpenses(propertyId: string): Promise<Expense[]> {
  const res = await apiFetch(`${API_BASE}/properties/${propertyId}/expenses`);
  return handleResponse<Expense[]>(res);
}

export async function createExpense(data: ExpenseCreateInput): Promise<Expense> {
  const res = await apiFetch(`${API_BASE}/expenses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Expense>(res);
}

export async function getProfitReport(propertyId: string): Promise<ProfitReport> {
  const res = await apiFetch(`${API_BASE}/properties/${propertyId}/profit`);
  return handleResponse<ProfitReport>(res);
}

export async function uploadPropertyImage(propertyId: string, file: File): Promise<Property> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await apiFetch(`${API_BASE}/properties/${propertyId}/image`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<Property>(res);
}

export async function getFiscalData(propertyId: string): Promise<FiscalData> {
  const res = await apiFetch(`${API_BASE}/properties/${propertyId}/fiscal-data`);
  return handleResponse<FiscalData>(res);
}

export async function updateFiscalData(
  propertyId: string,
  data: FiscalDataInput
): Promise<FiscalData> {
  const res = await apiFetch(`${API_BASE}/properties/${propertyId}/fiscal-data`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<FiscalData>(res);
}

export async function getLeaseContracts(propertyId: string): Promise<LeaseContract[]> {
  const res = await apiFetch(`${API_BASE}/properties/${propertyId}/contracts`);
  return handleResponse<LeaseContract[]>(res);
}

export async function createLeaseContract(propertyId: string, data: LeaseContractInput): Promise<LeaseContract> {
  const res = await apiFetch(`${API_BASE}/properties/${propertyId}/contracts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<LeaseContract>(res);
}

export async function updateLeaseContract(contractId: string, data: Partial<LeaseContractInput>): Promise<LeaseContract> {
  const res = await apiFetch(`${API_BASE}/contracts/${contractId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<LeaseContract>(res);
}

export async function deleteLeaseContract(contractId: string): Promise<void> {
  const res = await apiFetch(`${API_BASE}/contracts/${contractId}`, { method: "DELETE" });
  await handleResponse<void>(res);
}

export async function updateIncomeFiscalCategory(id: string, fiscalCategory: string): Promise<Income> {
  const res = await apiFetch(`${API_BASE}/incomes/${id}/fiscal-category`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fiscal_category: fiscalCategory }),
  });
  return handleResponse<Income>(res);
}

export async function updateExpenseFiscalCategory(id: string, fiscalCategory: string): Promise<Expense> {
  const res = await apiFetch(`${API_BASE}/expenses/${id}/fiscal-category`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fiscal_category: fiscalCategory }),
  });
  return handleResponse<Expense>(res);
}

import type { FiscalSuggestionsResponse, FiscalReport } from "../types";
export async function getFiscalSuggestions(propertyId: string): Promise<FiscalSuggestionsResponse> {
  const res = await apiFetch(`${API_BASE}/properties/${propertyId}/fiscal-suggestions`, {
    method: "POST"
  });
  return handleResponse<FiscalSuggestionsResponse>(res);
}

export async function getFiscalReport(propertyId: string, year: number): Promise<FiscalReport> {
  const res = await apiFetch(`${API_BASE}/properties/${propertyId}/fiscal-report?year=${year}`);
  return handleResponse<FiscalReport>(res);
}

export async function downloadFiscalReportPdf(propertyId: string, year: number): Promise<void> {
  const res = await apiFetch(
    `${API_BASE}/properties/${propertyId}/fiscal-report/pdf?year=${year}`
  );

  if (!res.ok) {
    const text = await res.text();
    try {
      const json = JSON.parse(text);
      throw new Error(json.detail || text);
    } catch {
      throw new Error(text || 'Error al descargar el PDF');
    }
  }

  const contentDisposition = res.headers.get('content-disposition');
  const filenameMatch = contentDisposition?.match(/filename="(.+)"/);
  const filename = filenameMatch ? filenameMatch[1] : `borrador_fiscal_${year}.pdf`;

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

