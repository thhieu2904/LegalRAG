/* Badge Component */
import type { ReactNode } from "react";
import { cn } from "../../../lib/utils";

interface BadgeProps {
  children: ReactNode;
  variant?: "primary" | "success" | "warning" | "error" | "neutral";
  className?: string;
}

export function Badge({
  children,
  variant = "neutral",
  className,
}: BadgeProps) {
  const variantClasses = {
    primary: "badge-primary",
    success: "badge-success",
    warning: "badge-warning",
    error: "badge-error",
    neutral: "badge-neutral",
  };

  return (
    <span className={cn("badge", variantClasses[variant], className)}>
      {children}
    </span>
  );
}
