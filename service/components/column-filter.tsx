"use client"

import { useState, useRef, useEffect, useMemo } from "react"
import { ChevronDown, ArrowUp, ArrowDown, X, Search } from "lucide-react"
import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"

interface ColumnFilterProps {
  selectedValues: string[]
  availableOptions: string[]
  sortDir: "asc" | "desc" | null
  isLocked: boolean
  lockedMessage?: string
  onFilterChange: (values: string[]) => void
  onSortChange: (dir: "asc" | "desc" | null) => void
}

export function ColumnFilter({
  selectedValues,
  availableOptions,
  sortDir,
  isLocked,
  lockedMessage,
  onFilterChange,
  onSortChange,
}: ColumnFilterProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState("")
  const triggerRef = useRef<HTMLButtonElement>(null)
  const popoverRef = useRef<HTMLDivElement>(null)
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null)

  useEffect(() => {
    if (open && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect()
      let left = Math.max(8, rect.left)
      const pw = 256
      if (left + pw > window.innerWidth - 8) left = window.innerWidth - pw - 8
      setPos({ top: rect.bottom + 4, left })
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const down = (e: MouseEvent) => {
      if (
        popoverRef.current && !popoverRef.current.contains(e.target as Node) &&
        triggerRef.current && !triggerRef.current.contains(e.target as Node)
      ) {
        setOpen(false); setSearch("")
      }
    }
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") { setOpen(false); setSearch("") }
    }
    document.addEventListener("mousedown", down)
    document.addEventListener("keydown", key)
    return () => {
      document.removeEventListener("mousedown", down)
      document.removeEventListener("keydown", key)
    }
  }, [open])

  const filteredOptions = useMemo(() => {
    if (!search) return availableOptions
    return availableOptions.filter(v => v.toLowerCase().includes(search.toLowerCase()))
  }, [availableOptions, search])

  const handleToggle = (value: string) => {
    const next = selectedValues.includes(value)
      ? selectedValues.filter(v => v !== value)
      : [...selectedValues, value]
    onFilterChange(next)
  }

  const handleClear = () => {
    onFilterChange([])
    setSearch("")
  }

  const hasFilter = selectedValues.length > 0

  return (
    <>
      <button
        ref={triggerRef}
        onClick={() => { if (!isLocked) setOpen(prev => !prev) }}
        className={cn(
          "relative inline-flex items-center justify-center w-5 h-5 rounded transition-colors flex-shrink-0",
          hasFilter ? "text-primary" : "text-muted-foreground hover:text-foreground",
          isLocked && "opacity-20 cursor-not-allowed"
        )}
        title={isLocked ? lockedMessage : undefined}
      >
        <ChevronDown className="w-3.5 h-3.5" />
        {hasFilter && (
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-primary" />
        )}
      </button>
      {open && !isLocked && pos && (
        <div
          ref={popoverRef}
          style={{ position: "fixed", top: pos.top, left: pos.left, zIndex: 9999 }}
          className="w-64 bg-card border border-border rounded-lg shadow-xl p-2 space-y-2"
        >
          <div className="flex items-center gap-1 pb-1 border-b border-border">
            <button
              onClick={() => onSortChange(sortDir === "asc" ? null : "asc")}
              className={cn(
                "flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors",
                sortDir === "asc" ? "bg-primary/20 text-primary" : "hover:bg-secondary text-muted-foreground"
              )}
            >
              <ArrowUp className="w-3 h-3" /> А→Я
            </button>
            <button
              onClick={() => onSortChange(sortDir === "desc" ? null : "desc")}
              className={cn(
                "flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors",
                sortDir === "desc" ? "bg-primary/20 text-primary" : "hover:bg-secondary text-muted-foreground"
              )}
            >
              <ArrowDown className="w-3 h-3" /> Я→А
            </button>
            <div className="flex-1" />
            <button
              onClick={handleClear}
              className="flex items-center gap-1 px-2 py-1 rounded text-xs hover:bg-destructive/10 text-destructive transition-colors"
            >
              <X className="w-3 h-3" /> Сброс
            </button>
          </div>

          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-muted-foreground" />
            <Input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Поиск..."
              className="pl-6 h-7 text-xs"
            />
          </div>

          <div className="flex items-center justify-between px-1">
            <span className="text-xs text-muted-foreground">
              {selectedValues.length} из {availableOptions.length}
            </span>
          </div>

          <div className="max-h-48 overflow-y-auto space-y-0.5">
            {filteredOptions.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-4">
                {search ? "Нет совпадений" : "Нет значений"}
              </p>
            ) : (
              filteredOptions.map(value => (
                <label
                  key={value}
                  className="flex items-center gap-2 px-2 py-1 rounded cursor-pointer hover:bg-secondary text-xs transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={selectedValues.includes(value)}
                    onChange={() => handleToggle(value)}
                    className="w-3.5 h-3.5 accent-primary"
                  />
                  <span className="truncate">{value || "(пусто)"}</span>
                </label>
              ))
            )}
          </div>
        </div>
      )}
    </>
  )
}
