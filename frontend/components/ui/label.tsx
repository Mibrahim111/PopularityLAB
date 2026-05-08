import { cn } from "@/lib/utils";

export function Label({
  className,
  htmlFor,
  children,
}: {
  htmlFor?: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <label
      htmlFor={htmlFor}
      className={cn("block text-[11px] font-medium uppercase tracking-wide text-muted-foreground", className)}
    >
      {children}
    </label>
  );
}
