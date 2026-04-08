"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Database, Brain, CheckCircle2, AlertCircle } from "lucide-react"
import type { PaymentRecord } from "@/app/page"

interface StatsPanelProps {
  records: PaymentRecord[]
}

export function StatsPanel({ records }: StatsPanelProps) {
  const totalRecords = records.length
  const fromCode = records.filter((r) => r.pl_source === "code").length
  const predicted = records.filter((r) => r.pl_source === "predicted").length
  const modified = records.filter((r) => r.isModified).length

  const plStats = records.reduce((acc, r) => {
    if (r.pl) {
      acc[r.pl] = (acc[r.pl] || 0) + 1
    }
    return acc
  }, {} as Record<string, number>)

  const topPL = Object.entries(plStats)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)

  const cfoStats = records.reduce((acc, r) => {
    if (r.cfo) {
      acc[r.cfo] = (acc[r.cfo] || 0) + 1
    }
    return acc
  }, {} as Record<string, number>)

  const topCFO = Object.entries(cfoStats)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <Card className="bg-card border-border">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Всего записей
          </CardTitle>
          <Database className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{totalRecords}</div>
        </CardContent>
      </Card>

      <Card className="bg-card border-border">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Из кода УФ
          </CardTitle>
          <CheckCircle2 className="h-4 w-4 text-primary" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-primary">{fromCode}</div>
          <p className="text-xs text-muted-foreground">
            {((fromCode / totalRecords) * 100).toFixed(1)}%
          </p>
        </CardContent>
      </Card>

      <Card className="bg-card border-border">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Предсказано ML
          </CardTitle>
          <Brain className="h-4 w-4 text-accent" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-accent">{predicted}</div>
          <p className="text-xs text-muted-foreground">
            {((predicted / totalRecords) * 100).toFixed(1)}%
          </p>
        </CardContent>
      </Card>

      <Card className="bg-card border-border">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Изменено
          </CardTitle>
          <AlertCircle className="h-4 w-4 text-warning" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-warning">{modified}</div>
          <p className="text-xs text-muted-foreground">
            Требует проверки
          </p>
        </CardContent>
      </Card>

      <Card className="bg-card border-border">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Топ-5 PL
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-1">
            {topPL.map(([pl, count]) => (
              <div key={pl} className="flex justify-between text-sm">
                <span className="font-mono">{pl}</span>
                <span className="text-muted-foreground">{count}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="bg-card border-border">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Топ-5 CFO
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-1">
            {topCFO.map(([cfo, count]) => (
              <div key={cfo} className="flex justify-between text-sm">
                <span className="font-mono truncate max-w-20">{cfo}</span>
                <span className="text-muted-foreground">{count}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
