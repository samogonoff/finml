"use client"

import { useState } from "react"
import { FileSpreadsheet } from "lucide-react"
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

interface DataTableProps {
  records: PaymentRecord[]
  onPLChange: (id: string, newPL: string) => void
  onCFOChange: (id: string, newCFO: string) => void
  isDataLoaded: boolean
  isLoading: boolean
}

export function DataTable({
  records,
  onPLChange,
  onCFOChange,
  isDataLoaded,
  isLoading,
}: DataTableProps) {
  const [editingPL, setEditingPL] = useState<string | null>(null)
  const [editingCFO, setEditingCFO] = useState<string | null>(null)
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(
    new Set(["num", "date", "recipient", "info", "amount_rub", "cfo", "pl", "code_uf"])
  )

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

  if (records.length === 0) {
    return (
      <Card className="p-12 bg-card border-border">
        <div className="flex flex-col items-center justify-center text-center">
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Нет результатов
          </h3>
          <p className="text-muted-foreground">
            Попробуйте изменить параметры поиска
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
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
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
              {allColumns
                .filter((col) => visibleColumns.has(col.key))
                .map((col) => (
                  <TableHead key={col.key} className={cn("text-muted-foreground", getColumnWidth(col.key))}>
                    {col.label}
                  </TableHead>
                ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {records.slice(0, 100).map((record) => (
              <TableRow
                key={record.id}
                className={cn(
                  "border-border transition-colors",
                  record.isModified && "bg-primary/5"
                )}
              >
                {allColumns
                  .filter((col) => visibleColumns.has(col.key))
                  .map((col) => {
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
        {records.length > 100 && (
          <div className="p-4 text-center text-muted-foreground text-sm">
            Показано 100 из {records.length} записей. Используйте поиск для фильтрации.
          </div>
        )}
      </Card>
    </div>
  )
}
