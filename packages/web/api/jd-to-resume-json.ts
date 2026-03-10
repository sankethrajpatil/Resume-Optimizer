import type { VercelRequest, VercelResponse } from "@vercel/node"

const MODEL = process.env.OPENAI_MODEL || "gpt-4.1-mini"
const API_KEY = process.env.OPENAI_API_KEY

type Skill = { name?: string; keywords?: string[] }
type Project = { name?: string; description?: string; keywords?: string[] }
type Sections = ("education" | "skills" | "work" | "projects" | "awards")[]
type ResumeJsonPayload = {
  sections: Sections
  skills: Skill[]
  projects: Project[]
}

deprecatedNoContent()
function deprecatedNoContent(): void {}

const systemPrompt = [
  "You are an expert product hiring manager and resume writer.",
  "You read a job description and output ONLY JSON for a resume builder form.",
  "The JSON must match this TypeScript shape (subset of FormValues):",
  "",
  "type Skill = { name?: string; keywords?: string[] }",
  "type Project = { name?: string; description?: string; keywords?: string[] }",
  "type Sections = ('education' | 'skills' | 'work' | 'projects' | 'awards')[]",
  "type Payload = {",
  "  sections: Sections;",
  "  skills: Skill[];",
  "  projects: Project[];",
  "}",
  "",
  "Rules for sections:",
  "- Always return sections in this exact order: ['education','skills','work','projects','awards'].",
  "",
  "Rules for skills:",
  "- Return exactly three skills objects, with these names:",
  "  1) 'Product & Strategy'",
  "  2) 'Data & Analytics'",
  "  3) 'Platforms & Tools'",
  "- For each, keywords MUST come from or be clearly implied by the JD.",
  "- Use concise, resume-ready phrases (e.g. 'roadmap ownership', 'inventory optimization').",
  "- Each keyword should be <= 40 characters and stand alone on one line in the resume.",
  "",
  "Rules for projects:",
  "- Return 2–3 projects that this candidate should highlight for this JD.",
  "- name: short, product-style project name.",
  "- description:",
  "  - EXACTLY ONE sentence, <= 120 characters including spaces.",
  "  - Must include at least one metric (%, count, time, revenue, or similar).",
  "  - Clear action + clear result, tailored to the JD.",
  "- keywords: 3–6 JD-aligned concepts for that project (e.g. 'inventory accuracy', 'store operations').",
  "",
  "Important:",
  "- ALWAYS respond with a single JSON object matching Payload.",
  "- Do NOT include comments, explanations, or Markdown — JSON only.",
].join("\n")

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed" })
    return
  }

  const jdText = (req.body?.jd_text || req.body?.text || "").toString().trim()
  if (!jdText) {
    res.status(400).json({ error: "jd_text is required" })
    return
  }

  if (!API_KEY) {
    res.status(500).json({ error: "OPENAI_API_KEY is not configured on the server" })
    return
  }

  try {
    const userPrompt = `Job description:\n"""${jdText}"""`

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
      res
        .status(502)
        .json({ error: "OpenAI API request failed", detail: errText || response.statusText })
      return
    }

    const data = await response.json()
    const content = data?.choices?.[0]?.message?.content

    if (!content) {
      res.status(502).json({ error: "OpenAI response missing content" })
      return
    }

    let payload: ResumeJsonPayload
    try {
      payload = JSON.parse(content) as ResumeJsonPayload
    } catch (e) {
      res.status(502).json({ error: "Failed to parse OpenAI JSON content", detail: String(e) })
      return
    }

    if (!Array.isArray(payload.sections) || payload.sections.length === 0) {
      payload.sections = ["education", "skills", "work", "projects", "awards"]
    }

    res.status(200).json(payload)
  } catch (e) {
    res.status(500).json({ error: "Unexpected server error", detail: String(e) })
  }
}
