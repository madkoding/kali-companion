import { type ReactNode } from "react";
import { Overlay } from "./Overlay";

interface Props {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  title?: string;
  size?: "md" | "xl";
  bare?: boolean;
}

export function Modal({ open, onClose, children, title, size = "md", bare = false }: Props) {
  return (
    <Overlay
      open={open}
      onClose={onClose}
      title={title}
      variant="modal"
      size={size}
      bare={bare}
    >
      {children}
    </Overlay>
  );
}
