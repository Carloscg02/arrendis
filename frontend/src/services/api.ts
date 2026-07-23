import type {
  Property,
  PropertyCreateInput,
  Income,
  IncomeCreateInput,
  Expense,
  ExpenseCreateInput,
  ProfitReport,
} from "../types";

const API_BASE = "http://localhost:8000/api";

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
  const res = await fetch(`${API_BASE}/properties`);
  return handleResponse<Property[]>(res);
}

export async function createProperty(data: PropertyCreateInput): Promise<Property> {
  const res = await fetch(`${API_BASE}/properties`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Property>(res);
}

export async function getPropertyById(id: string): Promise<Property> {
  const res = await fetch(`${API_BASE}/properties/${id}`);
  return handleResponse<Property>(res);
}

export async function deleteProperty(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/properties/${id}`, { method: "DELETE" });
  await handleResponse<void>(res);
}

export async function getIncomes(propertyId: string): Promise<Income[]> {
  const res = await fetch(`${API_BASE}/properties/${propertyId}/incomes`);
  return handleResponse<Income[]>(res);
}

export async function createIncome(data: IncomeCreateInput): Promise<Income> {
  const res = await fetch(`${API_BASE}/incomes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Income>(res);
}

export async function getExpenses(propertyId: string): Promise<Expense[]> {
  const res = await fetch(`${API_BASE}/properties/${propertyId}/expenses`);
  return handleResponse<Expense[]>(res);
}

export async function createExpense(data: ExpenseCreateInput): Promise<Expense> {
  const res = await fetch(`${API_BASE}/expenses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Expense>(res);
}

export async function getProfitReport(propertyId: string): Promise<ProfitReport> {
  const res = await fetch(`${API_BASE}/properties/${propertyId}/profit`);
  return handleResponse<ProfitReport>(res);
}

export async function uploadPropertyImage(propertyId: string, file: File): Promise<Property> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/properties/${propertyId}/image`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<Property>(res);
}
