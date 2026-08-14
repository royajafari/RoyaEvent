import * as React from "react"
import { Input as InputPrimitive } from "@base-ui/react/input"

import { cn } from "@/lib/utils"

function Input({ className, type, required, ...props }: React.ComponentProps<"input">) {
  return (
    <span className="relative block w-full">
      <InputPrimitive
        type={type}
        required={required}
        data-slot="input"
        className={cn(
          "h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-base transition-colors outline-none file:inline-flex file:h-6 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-input/50 disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 md:text-sm dark:bg-input/30 dark:disabled:bg-input/80 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40",
          className
        )}
        {...props}
      />
      {required && (
        <span
          aria-hidden="true"
          title="اجباری"
          className="pointer-events-none absolute top-0 right-0 h-2.5 w-2.5 bg-destructive"
          style={{ clipPath: "polygon(100% 0, 0 0, 100% 100%)" }}
        />
      )}
    </span>
  )
}

export { Input }
