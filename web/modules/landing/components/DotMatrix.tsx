import type { CSSProperties } from "react";

const N = 9;

// The logo's up-right arrow on a 9x9 grid. The value is the order each dot
// pops in: the diagonal from bottom-left, then both bars of the head together.
const ARROW = new Map<string, number>();
for (let c = 1; c <= 7; c++) ARROW.set(`${8 - c},${c}`, c - 1);
for (let k = 0; k < 4; k++) {
  ARROW.set(`1,${6 - k}`, 7 + k);
  ARROW.set(`${2 + k},7`, 7 + k);
}

function isNear(r: number, c: number) {
  if (r === 0 || c === 0 || r === N - 1 || c === N - 1) return false;
  for (let dr = -1; dr <= 1; dr++)
    for (let dc = -1; dc <= 1; dc++)
      if (ARROW.has(`${r + dr},${c + dc}`)) return true;
  return false;
}

/** Netra-style dot grid that draws the Content Importer arrow. Decorative. */
export function DotMatrix({ className }: { className?: string }) {
  const dots = [];
  for (let r = 0; r < N; r++) {
    for (let c = 0; c < N; c++) {
      const order = ARROW.get(`${r},${c}`);
      let size = "26%";
      let color = "oklch(0.92 0 0)";
      let cls = "";
      let style: CSSProperties = {};
      if (order !== undefined) {
        size = "42%";
        color = (r + c) % 3 ? "var(--foreground)" : "oklch(0.42 0 0)";
        cls = "dm-arrow";
        style = { "--i": order } as CSSProperties;
      } else if (isNear(r, c)) {
        size = "32%";
        color = "oklch(0.88 0 0)";
        if ((r * 3 + c) % 4 === 0) {
          cls = "dm-twinkle";
          style = {
            "--t": `${((r * 7 + c * 3) % 10) * 0.5}s`,
          } as CSSProperties;
        }
      }
      dots.push(
        <span key={`${r}-${c}`} className="flex items-center justify-center">
          <span
            className={`aspect-square rounded-full ${cls}`}
            style={{ width: size, background: color, ...style }}
          />
        </span>,
      );
    }
  }
  return (
    <div aria-hidden className={`aspect-square grid-cols-9 ${className ?? ""}`}>
      {dots}
    </div>
  );
}
