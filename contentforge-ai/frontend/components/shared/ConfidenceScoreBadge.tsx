import React from "react";
import { ShieldCheck, ShieldAlert, AlertTriangle } from "lucide-react";
import { clsx } from "clsx";

export interface ConfidenceScoreBadgeProps {
  score: number; // 0.0 - 1.0 or 0 - 100
  size?: "sm" | "md";
  className?: string;
}

export const ConfidenceScoreBadge: React.FC<ConfidenceScoreBadgeProps> = ({
  score,
  size = "md",
  className,
}) => {
  // Normalize score to percentage 0-100
  const normalizedScore = score <= 1.0 ? Math.round(score * 100) : Math.round(score);

  const isHigh = normalizedScore >= 90;
  const isMedium = normalizedScore >= 70 && normalizedScore < 90;

  const colorStyles = isHigh
    ? "bg-emerald-50 text-emerald-800 border-emerald-200"
    : isMedium
    ? "bg-amber-50 text-amber-800 border-amber-200"
    : "bg-rose-50 text-rose-800 border-rose-200";

  const Icon = isHigh ? ShieldCheck : isMedium ? AlertTriangle : ShieldAlert;

  return (
    <span
      data-testid="confidence-score-badge"
      title={`Validation Score: ${normalizedScore}%. Evaluated against Fact Registry by AI validation pass.`}
      className={clsx(
        "inline-flex items-center gap-1.5 font-semibold border rounded-full transition-colors",
        colorStyles,
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-xs",
        className
      )}
    >
      <Icon className={size === "sm" ? "w-3.5 h-3.5" : "w-4 h-4"} />
      <span>{normalizedScore}% source-grounded</span>
    </span>
  );
};
