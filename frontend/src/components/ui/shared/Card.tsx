/* Card Component */
import type { ReactNode } from "react";
import { cn } from "../../../lib/utils";

interface CardProps {
  children: ReactNode;
  className?: string;
}

interface CardHeaderProps {
  children: ReactNode;
  className?: string;
}

interface CardTitleProps {
  children: ReactNode;
  className?: string;
}

interface CardDescriptionProps {
  children: ReactNode;
  className?: string;
}

interface CardContentProps {
  children: ReactNode;
  className?: string;
}

interface CardFooterProps {
  children: ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return <div className={cn("card", className)}>{children}</div>;
}

export function CardHeader({ children, className }: CardHeaderProps) {
  return <div className={cn("card-header", className)}>{children}</div>;
}

export function CardTitle({ children, className }: CardTitleProps) {
  return <h3 className={cn("card-title", className)}>{children}</h3>;
}

export function CardDescription({ children, className }: CardDescriptionProps) {
  return <p className={cn("card-description", className)}>{children}</p>;
}

export function CardContent({ children, className }: CardContentProps) {
  return <div className={cn("card-content", className)}>{children}</div>;
}

export function CardFooter({ children, className }: CardFooterProps) {
  return <div className={cn("card-footer", className)}>{children}</div>;
}
