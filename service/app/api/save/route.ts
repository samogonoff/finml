import { NextRequest, NextResponse } from "next/server"
import { writeFile, mkdir } from "fs/promises"
import path from "path"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { records } = body

    if (!records || !Array.isArray(records)) {
      return NextResponse.json(
        { error: "Invalid records format" },
        { status: 400 }
      )
    }

    const exportDir = path.join(process.cwd(), "exports")
    await mkdir(exportDir, { recursive: true })

    const timestamp = new Date().toISOString().replace(/[:.]/g, "-")
    const jsonPath = path.join(exportDir, `finml-export-${timestamp}.json`)
    const csvPath = path.join(exportDir, `finml-export-${timestamp}.csv`)

    await writeFile(jsonPath, JSON.stringify(records, null, 2))

    const csvHeader = "id,Дата,Информация,Получатель,Сумма,CFO,PL,PL_source,CFO_source\n"
    const csvRows = records.map((r: any) =>
      [
        r.id,
        r.Дата,
        `"${(r.Информация || "").replace(/"/g, '""')}"`,
        `"${(r.Получатель || "").replace(/"/g, '""')}"`,
        r.Сумма,
        r.CFO,
        r.PL,
        r.PL_source,
        r.CFO_source,
      ].join(",")
    )
    await writeFile(csvPath, csvHeader + csvRows.join("\n"))

    return NextResponse.json({
      success: true,
      files: {
        json: jsonPath,
        csv: csvPath,
      },
      count: records.length,
    })
  } catch (error) {
    console.error("Save error:", error)
    return NextResponse.json(
      { error: "Failed to save data" },
      { status: 500 }
    )
  }
}
