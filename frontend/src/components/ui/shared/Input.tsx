/* Input Component */
import type { InputHTMLAttributes } from "react";
import { cn } from "../../../lib/utils";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
  helperText?: string;
  label?: string;
  required?: boolean;
}

export function Input({
  error = false,
  helperText,
  label,
  required = false,
  className,
  id,
  ...props
}: InputProps) {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");

  return (
    <div className="shared-input-group">
      {label && (
        <label
          htmlFor={inputId}
          className={cn(
            "shared-input-label",
            required && "shared-input-label--required"
          )}
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={cn(
          "shared-input",
          error && "shared-input--error",
          className
        )}
        {...props}
      />
      {helperText && (
        <span
          className={cn(error ? "shared-input-error" : "shared-input-help")}
        >
          {helperText}
        </span>
      )}
    </div>
  );
}
