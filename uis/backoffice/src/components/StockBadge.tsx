import { STOCK_LEVEL_LABELS, stockLevel } from "@/lib/inventory";

/** Stock level as icon + text + colour. */
export function StockBadge({ stock }: { stock: number }) {
  const level = stockLevel(stock);
  const { icon, text } = STOCK_LEVEL_LABELS[level];
  return (
    <span className={`badge ${level}`}>
      <span aria-hidden="true">{icon}</span> {text}
    </span>
  );
}
