export type Section = 'education' | 'skills' | 'work' | 'projects' | 'awards'

export interface Skill {
  name?: string
  keywords?: string[]
}

export interface Project {
  name?: string
  description?: string
  keywords?: string[]
}

export interface FormValues {
  sections: Section[]
  skills: Skill[]
  projects: Project[]
}
