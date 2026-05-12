import { NextRequest, NextResponse } from "next/server"
import { writeFile, mkdir } from "fs/promises"
import path from "path"
import { spawn } from "child_process"

interface PaymentRecord {
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
      const formData = await request.formData()
      const file = formData.get("file") as File

      if (!file) {
        resolve(NextResponse.json({ error: "No file provided" }, { status: 400 }))
        return
      }

      const bytes = await file.arrayBuffer()
      const buffer = Buffer.from(bytes)

      const uploadDir = path.join(process.cwd(), "uploads")
      await mkdir(uploadDir, { recursive: true })

      const filename = `${Date.now()}-${file.name.replace(/[^a-zA-Zа-яА-Я0-9.\-]/g, "_")}`
      const filepath = path.resolve(uploadDir, filename)
      await writeFile(filepath, buffer)

      const serviceDir = process.cwd()
      const projectDir = path.join(serviceDir, "..")
      const scriptPath = path.join(projectDir, "predict_excel_api.py")

      const python = spawn(process.platform === 'win32' ? "D:\\FinML\\.venv\\Scripts\\python.exe" : "python3", [scriptPath, filepath], {
        cwd: projectDir,
      })

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
          // Read from file path returned by Python
          const filepath = stdout.trim()
          const fs = await import('fs')
          const content = fs.readFileSync(filepath, 'utf-8')
          fs.unlinkSync(filepath) // Clean up
          
          const records: PaymentRecord[] = JSON.parse(content)
          const cleanRecords = records.map(r => ({
            ...r,
            pl: String(r.pl).replace(/\.0$/, ''),
            cfo: String(r.cfo).replace(/\.0$/, ''),
          }))
          resolve(new NextResponse(JSON.stringify({
            success: true,
            records: cleanRecords,
            filename,
          }), {
            headers: {
              'Content-Type': 'application/json; charset=utf-8',
            },
          }))
        } catch (e) {
          resolve(NextResponse.json(
            { error: "Failed to parse output" },
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
