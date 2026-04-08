import { spawnSync } from "child_process"
import path from "path"

interface PaymentRecord {
  Дата: string
  Информация: string
  Получатель: string
  Сумма: string
  PL: string
  CFO: string
  PL_source: "code" | "predicted"
  CFO_source: "code" | "predicted"
}

export async function predictCodes(filepath: string): Promise<PaymentRecord[]> {
  const serviceDir = process.cwd()
  const projectDir = path.join(serviceDir, "..")
  const scriptPath = path.join(projectDir, "predict_excel_api.py")
  
  console.log("serviceDir:", serviceDir)
  console.log("projectDir:", projectDir)
  console.log("scriptPath:", scriptPath)
  console.log("filepath:", filepath)
  
  const result = spawnSync("python3", [scriptPath, filepath], {
    cwd: projectDir,
    env: { ...process.env, HF_HUB_DISABLE_SYMLINKS: "1" },
    maxBuffer: 100 * 1024 * 1024,
  })
  
  if (result.status !== 0) {
    console.error("Python error:", result.stderr.toString())
    throw new Error(`Python script failed: ${result.stderr.toString()}`)
  }
  
  const output = result.stdout.toString()
  try {
    return JSON.parse(output)
  } catch (e) {
    console.error("JSON parse error")
    throw new Error("Failed to parse Python output")
  }
}
