/**
 * SeverityBadge - displays severity level with appropriate color
 */

import type { Severity } from "../api/types";

interface Props {
  severity: Severity;
  size?: "sm" | "md" | "lg";
}

const COLORS: Record<Severity, { bg: string; text: string }> = {
  low: { bg: "#22c55e", text: "#fff" },
  medium: { bg: "#f59e0b", text: "#000" },
  high: { bg: "#ef4444", text: "#fff" },
};

export function SeverityBadge({ severity, size = "md" }: Props) {
  const colors = COLORS[severity];
  const fontSize = size === "sm" ? 12 : size === "lg" ? 18 : 14;
  const padding = size === "sm" ? "2px 6px" : size === "lg" ? "6px 14px" : "4px 10px";

  return (
    <span
      style={{
        backgroundColor: colors.bg,
        color: colors.text,
        padding,
        borderRadius: 4,
        fontSize,
        fontWeight: 600,
        textTransform: "uppercase",
      }}
    >
      {severity}
    </span>
  );
}

