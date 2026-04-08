"use client"

import { Upload, Save, Database, Cpu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search, Loader2 } from "lucide-react"

interface HeaderProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  onLoadData: () => void
  onSaveData: () => void
  hasChanges: boolean
  isDataLoaded: boolean
  isLoading: boolean
}

export function Header({
  searchQuery,
  onSearchChange,
  onLoadData,
  onSaveData,
  hasChanges,
  isDataLoaded,
  isLoading,
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
            onClick={onLoadData}
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
