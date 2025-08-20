/* Button Component */
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "../../../lib/utils";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:
    | "primary"
    | "secondary"
    | "outline"
    | "ghost"
    | "success"
    | "warning"
    | "error";
  size?: "sm" | "md" | "lg" | "icon";
  children: ReactNode;
  loading?: boolean;
}

export function Button({
  variant = "primary",
  size = "md",
  children,
  loading = false,
  disabled,
  className,
  ...props
}: ButtonProps) {
  const baseClasses = "shared-button";
  const variantClasses = {
    primary: "shared-button--primary",
    secondary: "shared-button--secondary",
    outline: "shared-button--outline",
    ghost: "shared-button--ghost",
    success: "shared-button--success",
    warning: "shared-button--warning",
    error: "shared-button--error",
  };
  const sizeClasses = {
    sm: "shared-button--sm",
    md: "",
    lg: "shared-button--lg",
    icon: "shared-button--icon",
  };

  return (
    <button
      className={cn(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <span className="shared-button-spinner" />}
      {children}
    </button>
  );
}
