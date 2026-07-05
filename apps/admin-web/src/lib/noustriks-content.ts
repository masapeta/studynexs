/** Canonical copy, navigation, and product taxonomy for Noustriks marketing. */

/** Legal / ownership — single source for copyright notices in UI. */
export const LEGAL = {
  company: "Noustriks",
  owner: "Avinash Reddy Masapeta",
  ownerAlias: "ARM",
  productLine: "StudyNexs",
  license: "Proprietary",
  copyrightStartYear: 2026,
} as const;

export function copyrightNotice(year = new Date().getFullYear()): string {
  const start = LEGAL.copyrightStartYear;
  const range = year > start ? `${start}–${year}` : String(start);
  return `© ${range} ${LEGAL.company}. All rights reserved.`;
}

export const NOUSTRIKS = {
  name: "Noustriks",
  owner: LEGAL.owner,
  ownerAlias: LEGAL.ownerAlias,
  tagline: "Engineering Intelligent Systems for Tomorrow.",
  aboutTitle: "Building the Future of Intelligent Systems",
  description:
    "Noustriks is a deep technology company dedicated to building intelligent platforms that combine Artificial Intelligence, Persistent Memory, Quantum Computing, Cloud Infrastructure, and Enterprise Automation.",
  mission:
    "Rather than building software for the sake of software, we create products that help people and organizations think, learn, collaborate, and make better decisions.",
  visionTitle: "Engineering Intelligence Beyond Software",
  visionBody:
    "At Noustriks, we believe software should not simply automate tasks—it should understand context, retain knowledge, reason over information, and continuously improve. Our mission is to create intelligent systems that augment human capability across industries.",
  focusAreas: [
    {
      title: "Artificial Intelligence",
      description: "Agentic systems, LLMs, and production AI with human approval at every boundary.",
    },
    {
      title: "Persistent Memory",
      description: "Organizational knowledge that compounds across users, workflows, and time.",
    },
    {
      title: "Enterprise Infrastructure",
      description: "Cloud-native, multi-tenant platforms built for regulated environments.",
    },
  ],
} as const;

export const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/products", label: "Products" },
  { href: "/pricing", label: "Pricing" },
  { href: "/company", label: "Company" },
  { href: "/technology", label: "Technology" },
  { href: "/research", label: "Research" },
  { href: "/contact", label: "Contact" },
] as const;

export const STUDYNEXS = {
  slug: "studynexs",
  name: "StudyNexs",
  tagline: "The AI Operating System for Modern Schools.",
  shortDescription:
    "An AI-powered School Operating System that unifies principals, teachers, students, parents, and administrators in one intelligent ecosystem.",
  description:
    "StudyNexs transforms educational institutions into intelligent, connected ecosystems through AI-powered administration, teaching, learning, communication, and analytics.",
} as const;

export const STUDYNEXS_FEATURES = [
  "AI Tutor",
  "Student Management",
  "Attendance",
  "Admissions",
  "Assessments",
  "Homework",
  "Parent Communication",
  "AI Reports",
  "Analytics",
  "Finance",
  "HR",
  "Library",
  "Timetable",
  "Examination",
  "Transport",
  "Smart Notifications",
  "AI Insights",
  "Integrations",
] as const;

export const MEMORY_FABRIC = {
  slug: "memory-fabric",
  name: "Memory Fabric",
  tagline: "The Persistent Memory Layer for Intelligent Businesses.",
  shortDescription:
    "Enterprise memory infrastructure where AI agents, applications, and teams share long-term contextual knowledge.",
  description:
    "Memory Fabric is an enterprise memory platform that enables AI agents, applications, and teams to share long-term contextual knowledge across workflows.",
  extendedDescription:
    "Instead of isolated conversations and disconnected systems, Memory Fabric creates a persistent organizational intelligence layer where AI continuously remembers, reasons, and improves.",
} as const;

export const MEMORY_FABRIC_CAPABILITIES = [
  "Long-Term Memory",
  "Context Engineering",
  "Cross-Agent Memory",
  "Organizational Knowledge Graph",
  "User Memory",
  "Semantic Search",
  "Vector Search",
  "Retrieval-Augmented Memory",
  "Workflow Context",
  "Session Continuity",
  "Human Feedback Learning",
  "Agent Collaboration",
  "Memory Governance",
  "Multi-Tenant Architecture",
  "Role-Based Security",
  "Enterprise APIs",
  "Audit Logs",
  "Intelligent Retrieval",
] as const;

export const MEMORY_FABRIC_INDUSTRIES = [
  "Education",
  "Healthcare",
  "Banking",
  "Insurance",
  "Retail",
  "Manufacturing",
  "Logistics",
  "Government",
  "HR",
  "Legal",
  "Customer Support",
  "Enterprise Operations",
] as const;

export const FLAGSHIP_PRODUCTS = [
  {
    ...STUDYNEXS,
    href: "/products/studynexs",
    category: "Education",
    accent: "education" as const,
  },
  {
    ...MEMORY_FABRIC,
    href: "/products/memory-fabric",
    category: "Enterprise",
    accent: "enterprise" as const,
  },
] as const;

export const COMING_SOON_PRODUCTS = [
  {
    id: "studio",
    name: "Noustriks Studio",
    tagline: "Multi-Agent Development Platform",
    status: "Coming Soon",
  },
  {
    id: "research",
    name: "Noustriks Research",
    tagline: "AI Research · Persistent Memory · Quantum Computing",
    status: "In progress",
    href: "/research",
  },
  {
    id: "cloud",
    name: "Noustriks Cloud",
    tagline: "Cloud-native AI Infrastructure",
    status: "Coming Soon",
  },
] as const;

export const TECHNOLOGY_CATEGORIES = [
  {
    id: "ai",
    title: "Artificial Intelligence",
    items: [
      "Generative AI",
      "LLMs",
      "Agentic AI",
      "AI Agents",
      "Computer Vision",
      "NLP",
      "RAG",
      "Multimodal AI",
    ],
  },
  {
    id: "memory",
    title: "Memory Systems",
    items: [
      "Long-Term Memory",
      "Knowledge Graphs",
      "Context Engineering",
      "Semantic Search",
      "Vector Databases",
      "Organizational Intelligence",
      "Retrieval Systems",
    ],
  },
  {
    id: "quantum",
    title: "Quantum Computing",
    items: [
      "Quantum Algorithms",
      "Hybrid Quantum Systems",
      "Quantum Machine Learning",
      "Optimization",
      "Future Research",
    ],
  },
  {
    id: "engineering",
    title: "Engineering",
    items: [
      "Cloud Native",
      "Kubernetes",
      "Event-Driven Systems",
      "API Platforms",
      "Microservices",
      "Distributed Systems",
      "DevSecOps",
    ],
  },
  {
    id: "data",
    title: "Data",
    items: [
      "Data Engineering",
      "Analytics",
      "Data Lakes",
      "Data Pipelines",
      "Real-Time Processing",
    ],
  },
] as const;

export const RESEARCH_TOPICS = [
  {
    id: "ai",
    title: "AI Research",
    description: "Foundation models, agentic workflows, and systems designed for production—not demos.",
  },
  {
    id: "agentic",
    title: "Agentic Systems",
    description: "Multi-step workflows with tools, audit trails, and human gates at every publish boundary.",
  },
  {
    id: "memory",
    title: "Persistent Memory",
    description: "Architectures where organizational knowledge compounds instead of resetting each session.",
  },
  {
    id: "human-ai",
    title: "Human-AI Collaboration",
    description: "Interfaces where AI proposes and people approve before anything reaches students or customers.",
  },
  {
    id: "responsible",
    title: "Responsible AI",
    description: "Tenant isolation, purpose-bound data, and explainability for regulated industries.",
  },
  {
    id: "quantum",
    title: "Quantum Computing",
    description: "Hybrid classical–quantum research for optimization and next-generation compute.",
  },
  {
    id: "enterprise",
    title: "Enterprise Intelligence",
    description: "Memory layers and APIs that connect AI to real operational systems at scale.",
  },
] as const;

export const FOOTER_LINKS = {
  products: [
    { href: "/products/studynexs", label: "StudyNexs" },
    { href: "/products/memory-fabric", label: "Memory Fabric" },
    { href: "/products#roadmap", label: "Future Products" },
  ],
  company: [
    { href: "/company", label: "About" },
    { href: "/research", label: "Research" },
    { href: "/technology", label: "Technology" },
    { href: "/contact", label: "Contact" },
  ],
  studynexs: [
    { href: "/products/studynexs", label: "Product overview" },
    { href: "/platform", label: "Architecture" },
    { href: "/pricing", label: "Pricing" },
    { href: "/login?portal=staff", label: "Request demo" },
  ],
} as const;

export const CONTACT = {
  email: "hello@noustriks.com",
  headline: "Start a conversation",
  description:
    "Whether you are a school exploring StudyNexs, an enterprise evaluating Memory Fabric, or a partner interested in Noustriks — we respond thoughtfully.",
} as const;

export const HOME_HERO = {
  eyebrow: "Deep Technology",
  titleLine1: "Engineering intelligent",
  titleAccent: "systems that endure",
  lead: "Noustriks builds platforms at the intersection of artificial intelligence, persistent memory, and enterprise infrastructure — so organizations can think, learn, and operate with greater clarity.",
  primaryCta: { href: "/products", label: "Explore products" },
  secondaryCta: { href: "/company", label: "What we do" },
} as const;

export const HOME_CTA = {
  title: "Build with intelligence that lasts",
  lead: "From StudyNexs in education to Memory Fabric in enterprise — discover how Noustriks products share one commitment to human-approved AI.",
  primary: { href: "/contact", label: "Contact us" },
  secondary: { href: "/pricing", label: "View pricing" },
  tertiary: { href: "/products/studynexs", label: "StudyNexs demo" },
} as const;
