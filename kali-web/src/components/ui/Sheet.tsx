import { type ReactNode } from "react";
import { Overlay } from "./Overlay";

type Side = "left" | "right" | "bottom";

interface Props {
  side: Side;
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  title?: string;
}

export function Sheet({ side, open, onClose, children, title }: Props) {
  const variant = side === "bottom" ? "sheet-bottom" : side === "left" ? "sheet-left" : "sheet-right";

  return (
    <Overlay
      open={open}
      onClose={onClose}
      title={title}
      variant={variant}
      showHandle={side === "bottom"}
    >
      {children}
    </Overlay>
  );
}
