const themes = {
  VISA: "from-indigo-600 via-indigo-700 to-slate-900",
  MASTERCARD: "from-rose-500 via-orange-500 to-amber-500",
  CARD: "from-slate-600 to-slate-900",
};

export function brandOf(number = "") {
  const n = number.replace(/\s/g, "");
  if (/^4/.test(n)) return "VISA";
  if (/^(5[1-5]|2[2-7])/.test(n)) return "MASTERCARD";
  return "CARD";
}

// Groups typed digits in fours and pads the rest with dots for the live preview.
export function fmtNumber(raw = "") {
  const digits = raw.replace(/\D/g, "").padEnd(16, "•").slice(0, 16);
  return digits.match(/.{1,4}/g).join(" ");
}

export default function CardVisual({ brand = "CARD", number, holder, expiry, className = "" }) {
  const b = String(brand).toUpperCase();
  const shown = String(number || "").replace(/\*/g, "•");
  return (
    <div className={`relative aspect-[1.586/1] w-full max-w-sm overflow-hidden rounded-2xl bg-gradient-to-br p-5 text-white shadow-lg ${themes[b] || themes.CARD} ${className}`}>
      <div className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/10" />
      <div className="pointer-events-none absolute -bottom-16 -left-8 h-44 w-44 rounded-full bg-white/10" />
      <div className="relative flex h-full flex-col justify-between">
        <div className="flex items-center justify-between">
          <div className="h-7 w-10 rounded-md bg-gradient-to-br from-amber-200 to-amber-400" />
          <span className="text-sm font-bold tracking-widest">{b}</span>
        </div>
        <div className="text-xl font-medium tracking-[0.15em] sm:text-2xl">{shown}</div>
        <div className="flex items-end justify-between text-xs">
          <div>
            <div className="text-[10px] uppercase text-white/60">Card holder</div>
            <div className="truncate font-medium tracking-wide">{holder}</div>
          </div>
          <div className="text-right">
            <div className="text-[10px] uppercase text-white/60">Expires</div>
            <div className="font-medium">{expiry}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
