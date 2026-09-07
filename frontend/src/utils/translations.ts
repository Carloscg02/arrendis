// frontend/src/utils/translations.ts

export const INCOME_CATEGORY_LABELS: Record<string, string> = {
  rent: "Alquiler",
  deposit: "Fianza / Depósito",
  other: "Otros Ingresos",
};

export const EXPENSE_CATEGORY_LABELS: Record<string, string> = {
  repair: "Reparación y Conservación",
  tax: "Tributos / IBI",
  insurance: "Seguro",
  community_fee: "Comunidad",
  utility: "Suministros",
  mortgage: "Hipoteca / Intereses",
  other: "Otros Gastos",
};

export const FISCAL_EXPENSE_LABELS: Record<string, string> = {
  intereses_capital: "Intereses y Financiación",
  reparacion_conservacion: "Reparación y Conservación",
  tributos: "Tributos y Tasas",
  primas_seguros: "Primas de Seguros",
  servicios_suministros: "Servicios y Suministros",
  formalizacion: "Gastos de Formalización",
  dudoso_cobro: "Saldos de Dudoso Cobro",
  amortizacion_muebles: "Amortización de Muebles",
  otros_deducibles: "Otros Gastos Deducibles",
  no_deducible: "No Deducible",
};

export const FISCAL_INCOME_LABELS: Record<string, string> = {
  rendimiento_integro: "Rendimiento Íntegro",
  otros_ingresos: "Otros Ingresos Computables",
};

export const PROPERTY_TYPE_LABELS: Record<string, string> = {
  apartment: "Apartamento",
  house: "Casa",
  commercial: "Local Comercial",
  garage: "Garaje",
  land: "Terreno",
  other: "Otro",
};

export const PROPERTY_STATUS_LABELS: Record<string, string> = {
  available: "Disponible",
  rented: "Alquilado",
  maintenance: "Mantenimiento",
};

export const LEASE_TYPE_LABELS: Record<string, string> = {
  vivienda_habitual: "Vivienda Habitual",
  temporal: "Temporal",
  turistico: "Turístico",
  comercial: "Comercial",
};

export function translateIncomeCategory(cat?: string | null): string {
  if (!cat) return "";
  return INCOME_CATEGORY_LABELS[cat.toLowerCase()] || cat;
}

export function translateExpenseCategory(cat?: string | null): string {
  if (!cat) return "";
  return EXPENSE_CATEGORY_LABELS[cat.toLowerCase()] || cat;
}

export function translateFiscalCategory(cat?: string | null): string {
  if (!cat) return "";
  return FISCAL_EXPENSE_LABELS[cat] || FISCAL_INCOME_LABELS[cat] || cat.replace(/_/g, " ");
}

export function translatePropertyType(type?: string | null): string {
  if (!type) return "";
  return PROPERTY_TYPE_LABELS[type.toLowerCase()] || type;
}

export function translatePropertyStatus(status?: string | null): string {
  if (!status) return "";
  return PROPERTY_STATUS_LABELS[status.toLowerCase()] || status;
}

export function translateLeaseType(type?: string | null): string {
  if (!type) return "";
  return LEASE_TYPE_LABELS[type.toLowerCase()] || type;
}
