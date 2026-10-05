export function money(value, currency = "INR") {
  const n = Number(value);
  if (Number.isNaN(n)) return "-";
  try {
    return n.toLocaleString("en-IN", { style: "currency", currency });
  } catch {
    return `${currency} ${n.toFixed(2)}`;
  }
}

export function dateTime(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString("en-IN", {
    day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}
