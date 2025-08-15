import React from "react";

interface AvatarProps {
  className?: string;
  children: React.ReactNode;
}

interface AvatarImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src?: string;
}

interface AvatarFallbackProps {
  className?: string;
  children: React.ReactNode;
}

export function Avatar({ className = "", children }: AvatarProps) {
  return (
    <div
      className={`relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full ${className}`}
    >
      {children}
    </div>
  );
}

export function AvatarImage({ src, alt, ...props }: AvatarImageProps) {
  if (!src) return null;

  return (
    <img
      className="aspect-square h-full w-full"
      src={src}
      alt={alt}
      {...props}
    />
  );
}

export function AvatarFallback({
  className = "",
  children,
}: AvatarFallbackProps) {
  return (
    <div
      className={`flex h-full w-full items-center justify-center rounded-full bg-gray-100 ${className}`}
    >
      {children}
    </div>
  );
}
