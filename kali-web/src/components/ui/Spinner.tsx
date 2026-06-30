import { Loader2 } from "lucide-react";

interface Props {
  size?: number;
  className?: string;
  label?: string;
}

export function Spinner({ size = 18, className = "", label = "Loading" }: Props) {
  return (
    <Loader2
      size={size}
      className={`animate-spin ${className}`}
      role="status"
      aria-label={label}
    />
  );
}
