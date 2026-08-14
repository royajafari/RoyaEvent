import * as React from "react"

import { cn } from "@/lib/utils"

function Textarea({ className, required, ...props }: React.ComponentProps<"textarea">) {
  return (
    <span className="relative block w-full">
      <textarea
        required={required}
        data-slot="textarea"
        className={cn(
          "flex field-sizing-content min-h-16 w-full rounded-lg border border-input bg-transparent px-2.5 py-2 text-base transition-colors outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:bg-input/50 disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 md:text-sm dark:bg-input/30 dark:disabled:bg-input/80 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40",
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

export { Textarea }
