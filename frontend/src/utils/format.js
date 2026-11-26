const integerFormat = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
const rupeeFormat = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

const CRORE = 10000000;
const LAKH = 100000;

export const formatNumber = (value) => integerFormat.format(value ?? 0);

export const formatCurrency = (value) => rupeeFormat.format(value ?? 0);

export function formatCompactCurrency(value) {
  const amount = value ?? 0;
  if (amount >= CRORE) return `₹${(amount / CRORE).toFixed(2)} Cr`;
  if (amount >= LAKH) return `₹${(amount / LAKH).toFixed(2)} L`;
  return formatCurrency(amount);
}

export const formatRupeesPerKm = (value) => `₹${Number(value ?? 0).toFixed(2)}`;

export const formatScore = (value) => Number(value ?? 0).toFixed(1);

export const formatPercentValue = (value) => `${Number(value ?? 0).toFixed(1)}%`;

export const formatKilometres = (value) => `${formatNumber(value)} km`;

export const formatKilowattHours = (value) => `${Number(value ?? 0).toFixed(1)} kWh`;

export const formatEnergyPer100Km = (value) => `${Number(value ?? 0).toFixed(1)} kWh/100 km`;

export const formatPercent = (part, total) =>
  total > 0 ? `${((part / total) * 100).toFixed(1)}%` : "0%";

export const formatDate = (isoDate) =>
  new Date(`${isoDate}T00:00:00`).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

export const formatMonth = (isoMonth) =>
  new Date(`${isoMonth}-01T00:00:00`).toLocaleDateString("en-GB", {
    month: "short",
    year: "numeric",
  });
