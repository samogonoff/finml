"use client"

import { Upload, Save, Database, Cpu, FileSpreadsheet } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search, Loader2, ChevronDown } from "lucide-react"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const REGIONS = ["BR", "BY", "RU", "KZ", "UZ", "CN", "TR"] as const

interface HeaderProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  onLoadFrom1C: () => void
  onLoadExcel: () => void
  onSaveData: () => void
  hasChanges: boolean
  isDataLoaded: boolean
  isLoading: boolean
  dateFrom: string
  dateTo: string
  region: string
  onDateFromChange: (date: string) => void
  onDateToChange: (date: string) => void
  onRegionChange: (region: string) => void
}

export function Header({
  searchQuery,
  onSearchChange,
  onLoadFrom1C,
  onLoadExcel,
  onSaveData,
  hasChanges,
  isDataLoaded,
  isLoading,
  dateFrom,
  dateTo,
  region,
  onDateFromChange,
  onDateToChange,
  onRegionChange,
}: HeaderProps) {
  return (
    <header className="border-b border-border bg-card sticky top-0 z-50">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-primary">
            <Cpu className="w-5 h-5 text-primary-foreground" />
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-foreground text-sm leading-tight">
              FinML Классификатор
            </span>
            <span className="text-xs text-muted-foreground leading-tight">
              Предсказание кодов PL и CFO
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Select value={region} onValueChange={onRegionChange}>
            <SelectTrigger className="w-16 h-9 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {REGIONS.map((r) => (
                <SelectItem key={r} value={r} className="text-xs">
                  {r}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input
            type="date"
            value={dateFrom}
            onChange={(e) => onDateFromChange(e.target.value)}
            className="w-36 h-9 text-xs"
          />
          <Input
            type="date"
            value={dateTo}
            onChange={(e) => onDateToChange(e.target.value)}
            className="w-36 h-9 text-xs"
          />
        </div>

        <div className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Поиск по получателю или информации..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-9 bg-secondary border-border focus:ring-primary"
            />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={onLoadFrom1C}
            disabled={isLoading}
            className="gap-2"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Database className="w-4 h-4" />
            )}
            Загрузить данные
          </Button>
          <Button
            variant="outline"
            onClick={onLoadExcel}
            disabled={isLoading}
            className="gap-2"
          >
            <FileSpreadsheet className="w-4 h-4" />
            Excel
          </Button>
          <Button
            onClick={onSaveData}
            disabled={!hasChanges || isLoading}
            className="gap-2 bg-primary hover:bg-primary/90 text-primary-foreground font-medium"
          >
            <Save className="w-4 h-4" />
            Записать данные
          </Button>
        </div>
      </div>
    </header>
  )
}
