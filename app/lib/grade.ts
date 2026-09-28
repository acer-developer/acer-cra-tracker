// Grade -> band. Long-term scale (AAA..D) and short-term (A1+..A4/D) both map here.
// This is the single source of truth; the UI never recomputes it.
export type Band = "good" | "warning" | "serious" | "critical" | "unknown";

const GOOD = new Set(["AAA","AA","A","BBB","A1+","A1","A2+","A2"]);
const WARN = new Set(["BB","B","A3+","A3","A4+","A4","BB+","BB-","B+","B-"]);
const SERIOUS = new Set(["C","A4-"]);
const CRIT = new Set(["D"]);

export function bandForGrade(grade: string | null | undefined): Band {
  if (!grade) return "unknown";
  const g = grade.toUpperCase().replace(/\s+/g, "");
  // strip a leading modifier like "+"/"-" only after an exact-set miss
  if (GOOD.has(g)) return "good";
  if (WARN.has(g)) return "warning";
  if (SERIOUS.has(g)) return "serious";
  if (CRIT.has(g)) return "critical";
  // fall back on the base letter (drop +/-) so "AA-" etc. still classify
  const base = g.replace(/[+-]+$/, "");
  if (GOOD.has(base)) return "good";
  if (WARN.has(base)) return "warning";
  if (SERIOUS.has(base)) return "serious";
  if (CRIT.has(base)) return "critical";
  return "unknown";
}
