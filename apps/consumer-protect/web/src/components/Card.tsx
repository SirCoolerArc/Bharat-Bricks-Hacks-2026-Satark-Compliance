import { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: "sm" | "md" | "lg";
}

const PAD = { sm: "p-3", md: "p-5", lg: "p-7" };

export default function Card({ children, className = "", padding = "md" }: CardProps) {
  return (
    <div className={`card-surface ${PAD[padding]} ${className}`}>
      {children}
    </div>
  );
}
