"use client"

import * as React from "react"

import { cn } from "@/lib/utils"

const ToastContext = React.createContext<{
  toasts: Array<{ id: string; title?: string; description?: string; variant?: string }>
  addToast: (toast: { title?: string; description?: string; variant?: string }) => void
  removeToast: (id: string) => void
}>({
  toasts: [],
  addToast: () => {},
  removeToast: () => {},
})

export function Toaster() {
  const context = React.useContext(ToastContext)
  
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-md">
      {context.toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            "rounded-lg border bg-card p-4 shadow-lg animate-in slide-in-from-bottom-2",
            toast.variant === "error" && "border-destructive bg-destructive/10"
          )}
        >
          {toast.title && <div className="font-medium">{toast.title}</div>}
          {toast.description && (
            <div className="text-sm text-muted-foreground">{toast.description}</div>
          )}
        </div>
      ))}
    </div>
  )
}

export const useToast = () => {
  const context = React.useContext(ToastContext)
  return {
    toast: (options: { title?: string; description?: string; variant?: string }) => {
      context.addToast(options)
    },
  }
}

export { ToastContext }
