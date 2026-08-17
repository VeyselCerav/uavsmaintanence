import type { ReactNode } from "react";

import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

export function Field({
  label,
  className,
  children,
}: {
  label: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <Label className={cn("flex flex-col items-stretch gap-1.5 font-medium", className)}>
      {label}
      {children}
    </Label>
  );
}
