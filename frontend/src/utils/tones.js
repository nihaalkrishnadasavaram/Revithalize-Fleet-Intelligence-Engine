const STATUS_TONES = {
  Operational: "success",
  "Maintenance Due": "warning",
  "Needs Inspection": "orange",
  "High Risk": "danger",
};

const PRIORITY_TONES = {
  High: "danger",
  Medium: "warning",
  Low: "info",
};

const RISK_LEVEL_TONES = {
  Low: "success",
  Medium: "warning",
  High: "danger",
};

const HEALTH_STATUS_TONES = {
  Good: "success",
  "Needs Attention": "warning",
  Critical: "danger",
};

export const statusTone = (status) => STATUS_TONES[status] ?? "neutral";
export const priorityTone = (priority) => PRIORITY_TONES[priority] ?? "neutral";
export const riskLevelTone = (level) => RISK_LEVEL_TONES[level] ?? "neutral";
export const healthStatusTone = (status) => HEALTH_STATUS_TONES[status] ?? "neutral";

export function scoreTone(value, inverse = false) {
  if (inverse) {
    if (value >= 70) return "danger";
    if (value >= 40) return "warning";
    return "success";
  }
  if (value >= 75) return "success";
  if (value >= 50) return "warning";
  return "danger";
}
