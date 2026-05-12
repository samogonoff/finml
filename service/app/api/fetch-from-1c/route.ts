import { NextRequest, NextResponse } from "next/server"
import { spawn } from "child_process"
import path from "path"

interface Record {
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
  pl_source: string
  cfo_source: string
  is_modified: boolean
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  return new Promise(async (resolve) => {
    try {
      const { region, dateFrom, dateTo } = await request.json()

      if (!region || !dateFrom || !dateTo) {
        resolve(NextResponse.json(
          { error: "Missing required fields: region, dateFrom, dateTo" },
          { status: 400 }
        ))
        return
      }

      const projectDir = path.join(process.cwd(), "..")
      const scriptPath = path.join(projectDir, "fetch_and_predict.py")

      const python = spawn(
        process.platform === 'win32'
          ? "D:\\FinML\\.venv\\Scripts\\python.exe"
          : "python3",
        [scriptPath, region, dateFrom, dateTo],
        { cwd: projectDir }
      )

      let stdout = ""
      let stderr = ""

      python.stdout.on("data", (data: Buffer) => {
        stdout += new TextDecoder("utf-8", { fatal: false }).decode(data)
      })

      python.stderr.on("data", (data: Buffer) => {
        stderr += new TextDecoder("utf-8", { fatal: false }).decode(data)
      })

      python.on("close", async (code) => {
        if (code !== 0) {
          resolve(NextResponse.json(
            { error: `Python failed: ${stderr}` },
            { status: 500 }
          ))
          return
        }

        try {
          const outputPath = stdout.trim()
          const fs = await import('fs')
          const content = fs.readFileSync(outputPath, 'utf-8')
          fs.unlinkSync(outputPath)

          const records: Record[] = JSON.parse(content)
          const cleanRecords = records.map(r => ({
            ...r,
            pl: String(r.pl).replace(/\.0$/, ''),
            cfo: String(r.cfo).replace(/\.0$/, ''),
          }))
          resolve(new NextResponse(JSON.stringify({
            success: true,
            records: cleanRecords,
          }), {
            headers: {
              'Content-Type': 'application/json; charset=utf-8',
            },
          }))
        } catch (e) {
          resolve(NextResponse.json(
            { error: `Failed to parse output: ${e}` },
            { status: 500 }
          ))
        }
      })

      python.on("error", (err) => {
        resolve(NextResponse.json(
          { error: `Spawn error: ${err.message}` },
          { status: 500 }
        ))
      })
    } catch (error) {
      resolve(NextResponse.json(
        { error: String(error) },
        { status: 500 }
      ))
    }
  })
}
