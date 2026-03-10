import type { VercelRequest, VercelResponse } from "@vercel/node"
import { load } from "cheerio"
import type { ResumeData, SkillGroup, Project } from "@ats-resume/core"

const MODEL = process.env.OPENAI_MODEL || "gpt-4.1-mini"
const API_KEY = process.env.OPENAI_API_KEY

type AiSkill = { name?: string; keywords?: string[] }
type AiProject = { name?: string; description?: string; keywords?: string[] }
type AiPayload = {
  skills?: AiSkill[]
  projects?: AiProject[]
  sections?: string[]
  jobTitle?: string
  jobCompany?: string
}

type ParsedBody = {
  url?: string
  resume?: ResumeData
}

type ExtractedJob = {
  title: string
  text: string
}

function parseBody(req: VercelRequest): ParsedBody {
  const raw = req.body as any
  if (!raw) return {}
  if (typeof raw === "string") {
    try {
      return JSON.parse(raw)
    } catch {
      return {}
    }
  }
  return raw
}

function normalizeBullet(text: string): string {
  const clean = text.replace(/\s+/g, " ").trim()
  if (!clean) return ""
  if (clean.length <= 125) return clean
  const truncated = clean.slice(0, 125)
  const lastSpace = truncated.lastIndexOf(" ")
  return (lastSpace > 60 ? truncated.slice(0, lastSpace) : truncated).trim()
}

function toSkillGroups(aiSkills: AiSkill[] | undefined, fallback: SkillGroup[]): SkillGroup[] {
  if (aiSkills && aiSkills.length) {
    return aiSkills.map((s, idx) => ({
      group: s.name?.trim() || fallback[idx]?.group || `Skill ${idx + 1}`,
      items: (s.keywords ?? []).map((k) => k.trim()).filter(Boolean),
    }))
  }
  return fallback
}

function makeProjectBullets(p: AiProject): string[] {
  const bullets: string[] = []
  if (p.description) bullets.push(p.description)
  if (p.keywords?.length) {
    bullets.push(...p.keywords.map((k) => `Applied to ${k}`))
  }
  return bullets.map(normalizeBullet).filter(Boolean).slice(0, 3)
}

function toProjects(aiProjects: AiProject[] | undefined, fallback: Project[]): Project[] {
  if (aiProjects && aiProjects.length) {
    return aiProjects.map((p, idx) => {
      const base = fallback[idx] ?? fallback[0] ?? { title: "", stack: "", bullets: [], links: [] }
      return {
        title: p.name?.trim() || base.title,
        stack: base.stack || (p.keywords ?? []).join(", "),
        bullets: makeProjectBullets(p),
        links: base.links ?? [],
      }
    })
  }
  return fallback
}

async function extractJobFromUrl(url: string): Promise<ExtractedJob> {
  const res = await fetch(url, {
    headers: {
      "user-agent": "Mozilla/5.0 (compatible; ATSFlowBot/1.0; +https://github.com/fabriciotrinndade/ats-resume-generator-html)",
      accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    },
  })

  if (!res.ok) {
    throw new Error(`Failed to fetch URL (status ${res.status})`)
  }

  const html = await res.text()
  const $ = load(html)

  const metaTitle = $("meta[property='og:title']").attr("content")?.trim()
  const docTitle = $("title").first().text().trim()
  const h1Title = $("h1").first().text().trim()
  const title = metaTitle || h1Title || docTitle || "Job description"

  const metaDesc = $("meta[name='description']").attr("content")?.trim()
  const mainNodes = $("main, article, [role='main']").toArray()
  const targets = mainNodes.length ? mainNodes : [$("body").get(0)].filter(Boolean)

  const parts: string[] = []
  if (metaDesc) parts.push(metaDesc)
  for (const el of targets) {
    const text = $(el).text().replace(/\s+/g, " ").trim()
    if (text) parts.push(text)
  }

  const combined = [title, ...parts].filter(Boolean).join("\n")
  const text = combined.replace(/\n{2,}/g, "\n").trim().slice(0, 12000)

  if (!text) throw new Error("Could not extract text from page")

  return { title, text }
}

async function callModel(job: ExtractedJob, resume: ResumeData): Promise<AiPayload> {
  if (!API_KEY) throw new Error("OPENAI_API_KEY is not configured")

  const systemPrompt = [
    "You are an expert resume writer.",
    "Given a job description and the candidate's current projects, propose tailored skill keywords and rewritten project bullets.",
    "Respond ONLY with JSON matching this TypeScript type:",
    "",
    "type Skill = { name?: string; keywords?: string[] }",
    "type Project = { name?: string; description?: string; keywords?: string[] }",
    "type Payload = { skills: Skill[]; projects: Project[] }",
    "",
    "Rules:",
    "- Skills must align to the job and be concise, resume-ready phrases.",
    "- Projects: return 2-3 that best fit the job. description must be one sentence with a metric.",
    "- Each bullet you imply must stay under 125 characters; keep wording tight for Times New Roman at 10pt.",
    "- No markdown, no commentary — JSON only.",
  ].join("\n")

  const userPrompt = [
    `Job description text:\n"""${job.text}"""`,
    "",
    "Candidate projects (for context, rewrite as needed):",
    JSON.stringify(resume.projects ?? [], null, 2),
  ].join("\n")

  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${API_KEY}`,
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt },
      ],
      response_format: { type: "json_object" },
    }),
  })

  if (!response.ok) {
    const errText = await response.text().catch(() => "")
    throw new Error(errText || response.statusText)
  }

  const data = await response.json()
  const content = data?.choices?.[0]?.message?.content
  if (!content) throw new Error("Model response missing content")

  return JSON.parse(content) as AiPayload
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  try {
    if (req.method !== "POST") return res.status(405).json({ error: "Method not allowed" })

    const { url, resume } = parseBody(req)

    if (!url) return res.status(400).json({ error: "url is required" })
    if (!resume) return res.status(400).json({ error: "resume is required" })

    let job: ExtractedJob
    try {
      job = await extractJobFromUrl(url)
    } catch (e: any) {
      return res.status(422).json({ error: "Failed to scrape job page", detail: String(e?.message || e) })
    }

    let payload: AiPayload
    try {
      payload = await callModel(job, resume)
    } catch (e: any) {
      return res.status(502).json({ error: "Model call failed", detail: String(e?.message || e) })
    }

    const updatedResume: ResumeData = {
      ...resume,
      skills: toSkillGroups(payload.skills, resume.skills ?? []),
      projects: toProjects(payload.projects, resume.projects ?? []),
    }

    return res.status(200).json({
      job: {
        url,
        title: job.title,
        textPreview: job.text.slice(0, 800),
      },
      analysis: payload,
      resume: updatedResume,
    })
  } catch (e: any) {
    return res
      .status(500)
      .json({ error: "Unexpected server error", detail: String(e?.message || e) })
  }
}
