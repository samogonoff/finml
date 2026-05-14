"use client"

import { useState, useMemo, useEffect, useCallback } from "react"
import { FileSpreadsheet, ChevronLeft, ChevronRight, ArrowUp, ArrowDown } from "lucide-react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { PaymentRecord } from "@/app/page"
import { ColumnFilter } from "./column-filter"

interface DataTableProps {
  records: PaymentRecord[]
  searchQuery: string
  columnFilters: Record<string, string[]>
  sortConfig: { key: string; dir: "asc" | "desc" } | null
  onPLChange: (id: string, newPL: string) => void
  onCFOChange: (id: string, newCFO: string) => void
  onColumnFilterChange: (key: string, values: string[]) => void
  onSortChange: (config: { key: string; dir: "asc" | "desc" } | null) => void
  isDataLoaded: boolean
  isLoading: boolean
}

export function DataTable({
  records,
  searchQuery,
  columnFilters,
  sortConfig,
  onPLChange,
  onCFOChange,
  onColumnFilterChange,
  onSortChange,
  isDataLoaded,
  isLoading,
}: DataTableProps) {
  const [editingPL, setEditingPL] = useState<string | null>(null)
  const [editingCFO, setEditingCFO] = useState<string | null>(null)
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(
    new Set(["num", "date", "recipient", "info", "amount_rub", "cfo", "pl", "code_uf"])
  )
  const [pageIndex, setPageIndex] = useState(0)
  const [pageSize, setPageSize] = useState(50)

  if (!isDataLoaded || isLoading) {
    return (
      <Card className="p-12 bg-card border-border">
        <div className="flex flex-col items-center justify-center text-center">
          <FileSpreadsheet className="w-16 h-16 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Данные не загружены
          </h3>
          <p className="text-muted-foreground max-w-md">
            Нажмите кнопку &laquo;Загрузить данные&raquo; для выбора Excel файла
          </p>
        </div>
      </Card>
    )
  }

  const allColumns = [
    { key: "num", label: "№" },
    { key: "date", label: "Дата" },
    { key: "op_type", label: "Вид операции" },
    { key: "doc_type", label: "Тип документа" },
    { key: "details", label: "Реквизиты" },
    { key: "recipient", label: "Получатель" },
    { key: "info", label: "Информация" },
    { key: "amount_doc", label: "Сумма" },
    { key: "amount_rub", label: "Сумма руб" },
    { key: "currency", label: "Вал" },
    { key: "code_uf", label: "Код УФ" },
    { key: "department", label: "Подразделение" },
    { key: "debit", label: "Дебет" },
    { key: "credit", label: "Кредит" },
    { key: "cfo", label: "CFO" },
    { key: "pl", label: "PL" },
  ]

  const toggleColumn = (key: string) => {
    setVisibleColumns((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const getColumnWidth = (key: string): string => {
    switch (key) {
      case "num": return "w-12"
      case "date": return "w-24"
      case "op_type": return "w-32"
      case "doc_type": return "w-32"
      case "details": return "w-48"
      case "recipient": return "w-40"
      case "info": return "w-64"
      case "amount_doc": return "w-24"
      case "amount_rub": return "w-24"
      case "currency": return "w-12"
      case "code_uf": return "w-20"
      case "department": return "w-32"
      case "debit": return "w-24"
      case "credit": return "w-24"
      case "cfo": return "w-20"
      case "pl": return "w-16"
      default: return "w-auto"
    }
  }

  // Visible columns in display order (cascade order)
  const visibleColumnsList = useMemo(
    () => allColumns.filter(col => visibleColumns.has(col.key)),
    [visibleColumns]
  )
  const cascadeOrder = useMemo(() => visibleColumnsList.map(c => c.key), [visibleColumnsList])

  // Compute cascade-aware available options for a column
  const getAvailableOptions = useCallback((colKey: string): string[] => {
    const idx = cascadeOrder.indexOf(colKey)
    if (idx === -1) return []
    const leftKeys = cascadeOrder.slice(0, idx)

    let filtered = records
    for (const lk of leftKeys) {
      const sel = columnFilters[lk]
      if (sel && sel.length > 0) {
        filtered = filtered.filter(r => sel.includes(String(r[lk as keyof PaymentRecord] || "")))
      }
    }

    return [...new Set(filtered.map(r => String(r[colKey as keyof PaymentRecord] || "")))]
  }, [records, columnFilters, cascadeOrder])

  // Find rightmost active filter index (for lock logic)
  const rightmostActiveIdx = useMemo(() => {
    for (let i = cascadeOrder.length - 1; i >= 0; i--) {
      const sel = columnFilters[cascadeOrder[i]]
      if (sel && sel.length > 0) return i
    }
    return -1
  }, [columnFilters, cascadeOrder])

  const isColumnLocked = useCallback((colKey: string): boolean => {
    const idx = cascadeOrder.indexOf(colKey)
    if (idx === -1) return false
    for (let i = idx + 1; i < cascadeOrder.length; i++) {
      const sel = columnFilters[cascadeOrder[i]]
      if (sel && sel.length > 0) return true
    }
    return false
  }, [columnFilters, cascadeOrder])

  const getLockedMessage = (colKey: string): string | undefined => {
    const idx = cascadeOrder.indexOf(colKey)
    if (idx === -1) return undefined
    const lockedBy: string[] = []
    for (let i = idx + 1; i < cascadeOrder.length; i++) {
      const sel = columnFilters[cascadeOrder[i]]
      if (sel && sel.length > 0) {
        const col = allColumns.find(c => c.key === cascadeOrder[i])
        lockedBy.push(col?.label || cascadeOrder[i])
      }
    }
    if (lockedBy.length === 0) return undefined
    return `Сначала очистите фильтры: ${lockedBy.join(", ")}`
  }

  // Apply all filters + search + sort
  const processedRecords = useMemo(() => {
    let result = [...records]

    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      result = result.filter(r =>
        r.recipient.toLowerCase().includes(q) ||
        r.info.toLowerCase().includes(q) ||
        r.pl.toLowerCase().includes(q) ||
        r.cfo.toLowerCase().includes(q)
      )
    }

    for (const [key, values] of Object.entries(columnFilters)) {
      if (values.length > 0) {
        result = result.filter(r => {
          const rv = String(r[key as keyof PaymentRecord] || "")
          return values.includes(rv)
        })
      }
    }

    if (sortConfig) {
      result.sort((a, b) => {
        const aVal = String(a[sortConfig.key as keyof PaymentRecord] || "")
        const bVal = String(b[sortConfig.key as keyof PaymentRecord] || "")
        const cmp = aVal.localeCompare(bVal, "ru")
        return sortConfig.dir === "asc" ? cmp : -cmp
      })
    }

    return result
  }, [records, searchQuery, columnFilters, sortConfig])

  // Pagination
  const totalPages = Math.max(1, Math.ceil(processedRecords.length / pageSize))

  useEffect(() => {
    if (pageIndex >= totalPages) {
      setPageIndex(Math.max(0, totalPages - 1))
    }
  }, [totalPages, pageIndex])

  const paginatedRecords = useMemo(
    () => processedRecords.slice(pageIndex * pageSize, (pageIndex + 1) * pageSize),
    [processedRecords, pageIndex, pageSize]
  )

  if (processedRecords.length === 0) {
    return (
      <Card className="p-12 bg-card border-border">
        <div className="flex flex-col items-center justify-center text-center">
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Нет результатов
          </h3>
          <p className="text-muted-foreground">
            Попробуйте изменить параметры фильтрации или поиска
          </p>
        </div>
      </Card>
    )
  }

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-4">
        {allColumns.map((col) => (
          <button
            key={col.key}
            onClick={() => toggleColumn(col.key)}
            className={cn(
              "text-xs px-2 py-1 rounded border transition-colors",
              visibleColumns.has(col.key)
                ? "bg-primary text-primary-foreground border-primary"
                : "bg-secondary text-muted-foreground border-border hover:bg-secondary/80"
            )}
          >
            {col.label}
          </button>
        ))}
      </div>

      <Card className="bg-card border-border overflow-auto">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              {visibleColumnsList.map((col) => (
                <TableHead key={col.key} className={cn("text-muted-foreground", getColumnWidth(col.key))}>
                  <div className="flex items-center gap-0.5">
                    <span className="text-xs leading-none">{col.label}</span>
                    {sortConfig?.key === col.key && (
                      sortConfig.dir === "asc"
                        ? <ArrowUp className="w-3 h-3 text-primary flex-shrink-0" />
                        : <ArrowDown className="w-3 h-3 text-primary flex-shrink-0" />
                    )}
                    <ColumnFilter
                      selectedValues={columnFilters[col.key] || []}
                      availableOptions={getAvailableOptions(col.key)}
                      sortDir={sortConfig?.key === col.key ? sortConfig.dir : null}
                      isLocked={isColumnLocked(col.key)}
                      lockedMessage={getLockedMessage(col.key)}
                      onFilterChange={(values) => onColumnFilterChange(col.key, values)}
                      onSortChange={(dir) => onSortChange(dir ? { key: col.key, dir } : null)}
                    />
                  </div>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginatedRecords.map((record) => (
              <TableRow
                key={record.id}
                className={cn(
                  "border-border transition-colors",
                  record.isModified && "bg-primary/5"
                )}
              >
                {visibleColumnsList.map((col) => {
                  const value = record[col.key as keyof PaymentRecord]

                  if (col.key === "pl") {
                    return (
                      <TableCell key={col.key} className={getColumnWidth(col.key)}>
                        {editingPL === record.id ? (
                          <Input
                            value={record.pl}
                            onChange={(e) => onPLChange(record.id, e.target.value)}
                            onBlur={() => setEditingPL(null)}
                            onKeyDown={(e) => e.key === "Enter" && setEditingPL(null)}
                            className="h-7 w-14 font-mono text-xs"
                            autoFocus
                          />
                        ) : (
                          <div
                            onClick={() => setEditingPL(record.id)}
                            className={cn(
                              "px-2 py-1 rounded cursor-pointer hover:bg-secondary font-mono text-xs text-center",
                              record.pl_source === "code" ? "text-primary" : "text-foreground",
                              record.isModified && "bg-warning/20"
                            )}
                          >
                            {record.pl || "-"}
                          </div>
                        )}
                      </TableCell>
                    )
                  }

                  if (col.key === "cfo") {
                    return (
                      <TableCell key={col.key} className={getColumnWidth(col.key)}>
                        {editingCFO === record.id ? (
                          <Input
                            value={record.cfo}
                            onChange={(e) => onCFOChange(record.id, e.target.value)}
                            onBlur={() => setEditingCFO(null)}
                            onKeyDown={(e) => e.key === "Enter" && setEditingCFO(null)}
                            className="h-7 w-18 font-mono text-xs"
                            autoFocus
                          />
                        ) : (
                          <div
                            onClick={() => setEditingCFO(record.id)}
                            className={cn(
                              "px-2 py-1 rounded cursor-pointer hover:bg-secondary font-mono text-xs text-center",
                              record.cfo_source === "code" ? "text-primary" : "text-foreground",
                              record.isModified && "bg-warning/20"
                            )}
                          >
                            {record.cfo || "-"}
                          </div>
                        )}
                      </TableCell>
                    )
                  }

                  return (
                    <TableCell
                      key={col.key}
                      className={cn(
                        "text-xs",
                        getColumnWidth(col.key),
                        ["amount_doc", "amount_rub", "debit", "credit"].includes(col.key) && "text-right font-mono",
                        ["info", "details"].includes(col.key) && "max-w-xs truncate",
                        ["recipient"].includes(col.key) && "font-medium"
                      )}
                      title={["info", "details"].includes(col.key) ? String(value || "") : undefined}
                    >
                      {String(value || "")}
                    </TableCell>
                  )
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-3 px-1">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>Строк:</span>
          <select
            value={pageSize}
            onChange={(e) => { setPageSize(Number(e.target.value)); setPageIndex(0) }}
            className="bg-secondary border border-border rounded px-2 py-1 text-xs"
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={200}>200</option>
          </select>
        </div>
        <div className="text-xs text-muted-foreground">
          {pageIndex * pageSize + 1}–{Math.min((pageIndex + 1) * pageSize, processedRecords.length)} из {processedRecords.length}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setPageIndex(p => Math.max(0, p - 1))}
            disabled={pageIndex === 0}
            className="p-1 rounded hover:bg-secondary disabled:opacity-30 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-xs text-muted-foreground min-w-[3rem] text-center">
            {pageIndex + 1}/{totalPages}
          </span>
          <button
            onClick={() => setPageIndex(p => Math.min(totalPages - 1, p + 1))}
            disabled={pageIndex >= totalPages - 1}
            className="p-1 rounded hover:bg-secondary disabled:opacity-30 transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
