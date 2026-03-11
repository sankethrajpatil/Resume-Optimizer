import express from "express"
import type { Request, Response, NextFunction } from "express"
import { createServer as createViteServer } from "vite"
import path from "path"
import url from "url"
import jobLinkHandler from "./api/job-link-to-resume"
import jdHandler from "./api/jd-to-resume-json"

const __dirname = path.dirname(url.fileURLToPath(import.meta.url))

async function start() {
  const app = express()

  app.use(express.json({ limit: "2mb" }))

  // API routes (reuse Vercel handlers)
  app.post("/api/job-link-to-resume", (req: Request, res: Response) => {
    // Vercel handler uses req.method/body; express matches enough
    return jobLinkHandler(req as any, res as any)
  })

  app.post("/api/jd-to-resume-json", (req: Request, res: Response) => {
    return jdHandler(req as any, res as any)
  })

  // Vite in middleware mode for HMR + static
  const vite = await createViteServer({
    root: __dirname,
    server: { middlewareMode: true },
  })

  app.use(vite.middlewares)

  // Error handler
  app.use((err: any, _req: Request, res: Response, _next: NextFunction) => {
    console.error(err)
    res.status(500).json({ error: "Internal server error", detail: String(err?.message || err) })
  })

  const port = process.env.PORT ? Number(process.env.PORT) : 5174
  app.listen(port, () => {
    console.log(`Dev server (UI + API) listening on http://localhost:${port}`)
  })
}

start().catch((err) => {
  console.error("Failed to start dev server", err)
  process.exit(1)
})
