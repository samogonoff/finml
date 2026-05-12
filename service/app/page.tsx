"use client"

import { useState, useMemo, useRef } from "react"
import { Header } from "@/components/header"
import { DataTable } from "@/components/data-table"
import { StatsPanel } from "@/components/stats-panel"
import { toast as toastFn } from "sonner"

export interface PaymentRecord {
  id: string
  num: string
  op_type: string
  doc_type: string
  details: string
  date: string
  currency: string
  amount_doc: string
  amount_cur: string
  amount_rub: string
  info: string
  recipient: string
  code_uf: string
  department: string
  debit: string
  debit2: string
  credit: string
  credit2: string
  pl: string
  cfo: string
  pl_source: "code" | "predicted"
  cfo_source: "code" | "predicted"
  isModified: boolean
}

function todayStr() {
  const d = new Date()
  return d.toISOString().slice(0, 10)
}

function monthAgoStr() {
  const d = new Date()
  d.setMonth(d.getMonth() - 1)
  return d.toISOString().slice(0, 10)
}

export default function FinMLPage() {
  const [records, setRecords] = useState<PaymentRecord[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [region, setRegion] = useState("RU")
  const [dateFrom, setDateFrom] = useState(monthAgoStr)
  const [dateTo, setDateTo] = useState(todayStr)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const hasChanges = useMemo(() => {
    return records.some((r) => r.isModified)
  }, [records])

  const filteredRecords = useMemo(() => {
    if (!searchQuery) return records
    const query = searchQuery.toLowerCase()
    return records.filter(
      (r) =>
        r.recipient.toLowerCase().includes(query) ||
        r.info.toLowerCase().includes(query) ||
        r.pl.toLowerCase().includes(query) ||
        r.cfo.toLowerCase().includes(query)
    )
  }, [records, searchQuery])

  const handleLoadExcel = () => {
    fileInputRef.current?.click()
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsLoading(true)
    try {
      const formData = new FormData()
      formData.append("file", file)

      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) throw new Error("Upload failed")

      const data = await response.json()
      
      const processed: PaymentRecord[] = data.records.map((r: any, idx: number) => ({
        id: String(idx),
        num: r.num || "",
        op_type: r.op_type || "",
        doc_type: r.doc_type || "",
        details: r.details || "",
        date: r.date || "",
        currency: r.currency || "",
        amount_doc: r.amount_doc || "",
        amount_cur: r.amount_cur || "",
        amount_rub: r.amount_rub || "",
        info: r.info || "",
        recipient: r.recipient || "",
        code_uf: r.code_uf || "",
        department: r.department || "",
        debit: r.debit || "",
        debit2: r.debit2 || "",
        credit: r.credit || "",
        credit2: r.credit2 || "",
        pl: r.pl || "",
        cfo: r.cfo || "",
        pl_source: r.pl_source || "predicted",
        cfo_source: r.cfo_source || "predicted",
        isModified: r.is_modified || false,
      }))

      setRecords(processed)
      toastFn.success("Данные загружены", {
        description: `Загружено ${processed.length} записей`,
      })
    } catch (error) {
      toastFn.error("Ошибка загрузки", {
        description: "Не удалось загрузить файл",
      })
    } finally {
      setIsLoading(false)
      if (fileInputRef.current) fileInputRef.current.value = ""
    }
  }

  const handleLoadFrom1C = async () => {
    if (!dateFrom || !dateTo) {
      toastFn.error("Укажите даты")
      return
    }
    if (dateFrom > dateTo) {
      toastFn.error("Начальная дата позже конечной")
      return
    }

    setIsLoading(true)
    try {
      const dateFromStr = dateFrom.replace(/-/g, "")
      const dateToStr = dateTo.replace(/-/g, "")

      const response = await fetch("/api/fetch-from-1c", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ region, dateFrom: dateFromStr, dateTo: dateToStr }),
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.error || "Fetch failed")
      }

      const data = await response.json()
      
      const processed: PaymentRecord[] = data.records.map((r: any, idx: number) => ({
        id: String(idx),
        num: r.num || "",
        op_type: r.op_type || "",
        doc_type: r.doc_type || "",
        details: r.details || "",
        date: r.date || "",
        currency: r.currency || "",
        amount_doc: r.amount_doc || "",
        amount_cur: r.amount_cur || "",
        amount_rub: r.amount_rub || "",
        info: r.info || "",
        recipient: r.recipient || "",
        code_uf: r.code_uf || "",
        department: r.department || "",
        debit: r.debit || "",
        debit2: r.debit2 || "",
        credit: r.credit || "",
        credit2: r.credit2 || "",
        pl: r.pl || "",
        cfo: r.cfo || "",
        pl_source: r.pl_source || "predicted",
        cfo_source: r.cfo_source || "predicted",
        isModified: r.is_modified || false,
      }))

      setRecords(processed)
      toastFn.success("Данные загружены", {
        description: `Загружено ${processed.length} записей из 1С (${region})`,
      })
    } catch (error) {
      toastFn.error("Ошибка загрузки", {
        description: String(error),
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handlePLChange = (id: string, newPL: string) => {
    setRecords((prev) =>
      prev.map((r) =>
        r.id === id ? { ...r, pl: newPL, isModified: true } : r
      )
    )
  }

  const handleCFOChange = (id: string, newCFO: string) => {
    setRecords((prev) =>
      prev.map((r) =>
        r.id === id ? { ...r, cfo: newCFO, isModified: true } : r
      )
    )
  }

  const handleSaveData = async () => {
    try {
      const response = await fetch("/api/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ records }),
      })

      if (!response.ok) throw new Error("Save failed")

      setRecords((prev) =>
        prev.map((r) => ({ ...r, isModified: false }))
      )
      
      toastFn.success("Данные сохранены", {
        description: `Сохранено ${records.length} записей`,
      })
    } catch (error) {
      toastFn.error("Ошибка сохранения", {
        description: "Не удалось сохранить данные",
      })
    }
  }

  return (
    <>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept=".xlsx,.xls"
        className="hidden"
      />
      
      <Header
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onLoadFrom1C={handleLoadFrom1C}
        onLoadExcel={handleLoadExcel}
        onSaveData={handleSaveData}
        hasChanges={hasChanges}
        isDataLoaded={records.length > 0}
        isLoading={isLoading}
        dateFrom={dateFrom}
        dateTo={dateTo}
        region={region}
        onDateFromChange={setDateFrom}
        onDateToChange={setDateTo}
        onRegionChange={setRegion}
      />
      
      <main className="container mx-auto px-4 py-6">
        {records.length > 0 && (
          <StatsPanel records={records} />
        )}
        <DataTable
          records={filteredRecords}
          onPLChange={handlePLChange}
          onCFOChange={handleCFOChange}
          isDataLoaded={records.length > 0}
          isLoading={isLoading}
        />
      </main>
    </>
  )
}
