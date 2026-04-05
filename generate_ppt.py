"""Generate RxScope Client Presentation PPT"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Colors
DARK_BG = RGBColor(0x0F, 0x17, 0x2A)       # Deep navy
ACCENT_BLUE = RGBColor(0x3B, 0x82, 0xF6)   # Bright blue
ACCENT_GREEN = RGBColor(0x10, 0xB9, 0x81)   # Green
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0x94, 0xA3, 0xB8)
MEDIUM_GRAY = RGBColor(0x64, 0x74, 0x8B)
CARD_BG = RGBColor(0x1E, 0x29, 0x3B)        # Slightly lighter navy
ORANGE = RGBColor(0xF5, 0x9E, 0x0B)
RED = RGBColor(0xEF, 0x44, 0x44)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

def add_bg(slide, color=DARK_BG):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_text(slide, left, top, width, height, text, font_size=18, color=WHITE, bold=False, alignment=PP_ALIGN.LEFT, font_name="Calibri"):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    return txBox

def add_bullet_list(slide, left, top, width, height, items, font_size=16, color=WHITE, bullet_color=ACCENT_BLUE):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = f"  •  {item}"
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.font.name = "Calibri"
        p.space_after = Pt(8)
    return txBox

def add_card(slide, left, top, width, height, color=CARD_BG):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape

def add_accent_line(slide, left, top, width):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(0.04))
    shape.fill.solid()
    shape.fill.fore_color.rgb = ACCENT_BLUE
    shape.line.fill.background()

# ============ SLIDE 1: TITLE ============
slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank
add_bg(slide)
add_accent_line(slide, 1.5, 2.2, 2)
add_text(slide, 1.5, 2.4, 10, 1.2, "RxScope", font_size=54, bold=True, color=WHITE)
add_text(slide, 1.5, 3.5, 10, 0.8, "AI-Based Medical Content Identification System", font_size=28, color=ACCENT_BLUE)
add_text(slide, 1.5, 4.5, 10, 0.5, "Architecture & Technical Proposal for RxNetwork", font_size=18, color=LIGHT_GRAY)
add_text(slide, 1.5, 5.5, 5, 0.4, "April 2026  •  Confidential", font_size=14, color=MEDIUM_GRAY)

# ============ SLIDE 2: THE PROBLEM ============
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, 1, 0.4, 11, 0.6, "The Problem", font_size=36, bold=True, color=WHITE)
add_accent_line(slide, 1, 1.0, 1.5)

add_card(slide, 1, 1.4, 5.4, 2.8)
add_text(slide, 1.3, 1.6, 5, 0.4, "Current Industry Gap", font_size=20, bold=True, color=ACCENT_BLUE)
add_bullet_list(slide, 1.3, 2.1, 5, 2, [
    "Brand safety vendors (IAS, DoubleVerify) classify to AVOID content",
    "No solution classifies to SEEK HCP-targeted content",
    "No medical entity resolution (NPI, UMLS, drug names)",
    "No HCP vs consumer content distinction",
])

add_card(slide, 6.8, 1.4, 5.4, 2.8)
add_text(slide, 7.1, 1.6, 5, 0.4, "What RxNetwork Needs", font_size=20, bold=True, color=ACCENT_GREEN)
add_bullet_list(slide, 7.1, 2.1, 5, 2, [
    "AI-driven classification of medically relevant, HCP-oriented content",
    "Across Scribd, Slideshare & other platforms",
    "Pharmaceutical ad-targeting whitelist (CSV/XLSX)",
    "Entity verification: physicians, pharma, medical institutions",
])

add_card(slide, 1, 4.6, 11.2, 2.4)
add_text(slide, 1.3, 4.8, 10, 0.4, "RxScope Fills This Gap", font_size=22, bold=True, color=ORANGE)
add_bullet_list(slide, 1.3, 5.3, 10, 1.5, [
    "Medical taxonomy grounding (MeSH, ICD-10, DSM-5, IAB 3.1)",
    "NPI-verified physician identification via federal registry",
    "Document-level AI analysis with confidence scoring",
    "Programmatic ad-tech output format (CSV/XLSX + REST API)",
], font_size=16)

# ============ SLIDE 3: HOW IT WORKS ============
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, 1, 0.4, 11, 0.6, "How RxScope Works", font_size=36, bold=True, color=WHITE)
add_accent_line(slide, 1, 1.0, 1.5)

steps = [
    ("1", "Discover", "Crawl sitemaps &\nURL queues from\ntarget platforms", ACCENT_BLUE),
    ("2", "Scrape", "Fetch content via\nLightpanda (fast,\nrobots.txt compliant)", ACCENT_BLUE),
    ("3", "Extract", "Clean text, metadata,\nauthor info from\nHTML/PDF/PPT", ACCENT_BLUE),
    ("4", "Classify", "AI classification\nvia Claude + scispaCy\n+ MeSH/IAB mapping", ACCENT_GREEN),
    ("5", "Verify", "Entity resolution:\nNPI, RxNorm, FDA\nverification", ACCENT_GREEN),
    ("6", "Score", "Confidence scoring\n+ human review for\nedge cases", ORANGE),
    ("7", "Deliver", "CSV/XLSX whitelist\n+ REST API\n+ Dashboard", ORANGE),
]

for i, (num, title, desc, color) in enumerate(steps):
    x = 0.6 + i * 1.75
    add_card(slide, x, 1.5, 1.55, 3.5)
    # Number circle
    circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.55), Inches(1.7), Inches(0.45), Inches(0.45))
    circle.fill.solid()
    circle.fill.fore_color.rgb = color
    circle.line.fill.background()
    tf = circle.text_frame
    tf.paragraphs[0].text = num
    tf.paragraphs[0].font.size = Pt(16)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = WHITE
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.word_wrap = False
    
    add_text(slide, x + 0.15, 2.3, 1.3, 0.4, title, font_size=15, bold=True, color=color, alignment=PP_ALIGN.CENTER)
    add_text(slide, x + 0.1, 2.8, 1.4, 1.8, desc, font_size=11, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Arrow indicators between steps
for i in range(6):
    x = 0.6 + (i+1) * 1.75 - 0.25
    add_text(slide, x, 2.8, 0.3, 0.4, "→", font_size=20, color=MEDIUM_GRAY, alignment=PP_ALIGN.CENTER)

add_card(slide, 1, 5.4, 11.2, 1.6)
add_text(slide, 1.3, 5.5, 10, 0.4, "Key Differentiator", font_size=18, bold=True, color=ACCENT_BLUE)
add_text(slide, 1.3, 5.95, 10, 0.8, "Multi-agent AI pipeline powered by LangGraph orchestrates specialized agents for each step.\nClaude Sonnet handles volume classification; Claude Opus handles edge cases. Human-in-the-loop for quality assurance.", font_size=14, color=LIGHT_GRAY)

# ============ SLIDE 4: TECHNOLOGY STACK ============
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, 1, 0.4, 11, 0.6, "Technology Stack", font_size=36, bold=True, color=WHITE)
add_accent_line(slide, 1, 1.0, 1.5)

stack_items = [
    ("AI & Classification", [
        "Claude Sonnet 4 + Opus 4 (Anthropic)",
        "LangGraph — agent orchestration (open-source)",
        "LangSmith — monitoring & observability",
        "scispaCy + MedSpaCy — medical NLP",
        "BiomedBERT — biomedical embeddings",
    ], ACCENT_BLUE),
    ("Data & Storage", [
        "Supabase Pro — PostgreSQL 16 + pgvector",
        "Mumbai region (lowest latency for India)",
        "Upstash Redis — caching & job queues",
        "Cloudflare R2 — object storage (zero egress)",
    ], ACCENT_GREEN),
    ("Infrastructure", [
        "Lightpanda — fast, compliant web scraping",
        "Cloudflare Workers — edge API ($5/mo)",
        "Cloudflare Pages — dashboard hosting ($0)",
        "BrightData — rotating residential proxies",
    ], ORANGE),
    ("Medical APIs (All FREE)", [
        "NPI Registry — physician verification",
        "RxNorm — drug name resolution",
        "FDA NDC — drug identification",
        "UMLS — medical concept crosswalk",
        "MeSH — medical subject headings",
    ], RGBColor(0xA7, 0x8B, 0xFA)),
]

for i, (title, items, color) in enumerate(stack_items):
    x = 0.8 + (i % 4) * 3.05
    y = 1.4
    add_card(slide, x, y, 2.85, 3.6)
    add_text(slide, x + 0.15, y + 0.15, 2.6, 0.4, title, font_size=16, bold=True, color=color, alignment=PP_ALIGN.CENTER)
    # Separator line 
    sep = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x + 0.3), Inches(y + 0.55), Inches(2.2), Inches(0.02))
    sep.fill.solid()
    sep.fill.fore_color.rgb = color
    sep.line.fill.background()
    add_bullet_list(slide, x + 0.15, y + 0.65, 2.6, 2.8, items, font_size=11, color=LIGHT_GRAY)

add_card(slide, 0.8, 5.3, 11.6, 1.8)
add_text(slide, 1.1, 5.4, 11, 0.4, "LangGraph vs LangSmith — They Are DIFFERENT", font_size=18, bold=True, color=ACCENT_BLUE)
add_text(slide, 1.1, 5.85, 5, 1, "LangGraph = the ENGINE (builds the AI pipeline)\n  • Open-source, MIT license, $0 cost\n  • Orchestrates agents: scrape → classify → score", font_size=13, color=LIGHT_GRAY)
add_text(slide, 6.5, 5.85, 5.5, 1, "LangSmith = the DASHBOARD (monitors the pipeline)\n  • SaaS platform, free tier available\n  • Traces every decision, measures cost & accuracy", font_size=13, color=LIGHT_GRAY)

# ============ SLIDE 5: DATABASE DECISION ============
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, 1, 0.4, 11, 0.6, "Database & Hosting Decision", font_size=36, bold=True, color=WHITE)
add_accent_line(slide, 1, 1.0, 1.5)

add_text(slide, 1, 1.3, 11, 0.4, "PostgreSQL + pgvector (on Supabase Pro) — NOT MongoDB", font_size=22, bold=True, color=ACCENT_GREEN)

# Comparison cards
add_card(slide, 1, 1.9, 5.5, 3.2)
add_text(slide, 1.3, 2.0, 5, 0.4, "✅  PostgreSQL + pgvector", font_size=18, bold=True, color=ACCENT_GREEN)
add_bullet_list(slide, 1.3, 2.5, 5, 2.5, [
    "Native vector search — single DB for everything",
    "Full ACID compliance — no duplicate URLs",
    "Foreign keys for entity relationships",
    "SQL → CSV export (client requirement)",
    "LangGraph first-class checkpointer",
    "Supabase Pro: Mumbai region, $25/mo",
], font_size=13)

add_card(slide, 6.8, 1.9, 5.5, 3.2)
add_text(slide, 7.1, 2.0, 5, 0.4, "❌  MongoDB (Rejected)", font_size=18, bold=True, color=RED)
add_bullet_list(slide, 7.1, 2.5, 5, 2.5, [
    "Separate Atlas Vector Search needed ($$$)",
    "No JOINs — denormalized data mess",
    "Limited multi-doc transactions",
    "Complex aggregation for CSV export",
    "No official LangGraph checkpointer",
    "Wrong tool for relational medical data",
], font_size=13)

add_card(slide, 1, 5.4, 11.2, 1.7)
add_text(slide, 1.3, 5.5, 10, 0.4, "Supabase Pro — Key Facts", font_size=18, bold=True, color=ACCENT_BLUE)
add_text(slide, 1.3, 5.95, 5, 0.8, "• Mumbai region (ap-south-1) — India data residency\n• NOT blocked in India — fully accessible\n• pgvector built-in, PgBouncer connection pooling\n• Built-in dashboard for DB monitoring", font_size=13, color=LIGHT_GRAY)
add_text(slide, 7, 5.95, 5, 0.8, "• $25/mo base + $10 compute (with $10 credit)\n• 8GB disk included in Pro plan\n• Auth, Storage, Edge Functions included\n• Scales to 16XL ($3,730/mo) if needed", font_size=13, color=LIGHT_GRAY)

# ============ SLIDE 6: WHAT YOU GET ============
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, 1, 0.4, 11, 0.6, "What RxNetwork Gets", font_size=36, bold=True, color=WHITE)
add_accent_line(slide, 1, 1.0, 1.5)

deliverables = [
    ("🔍", "AI Classification System", "Automated identification of HCP-oriented\ncontent across multiple platforms"),
    ("📊", "Excel-Compatible Whitelist", "Deduplicated URL list in CSV/XLSX\nwith full metadata & confidence scores"),
    ("🖥️", "Admin Dashboard", "Real-time monitoring, search, export,\nand human-in-the-loop review panel"),
    ("🔗", "REST API", "Programmatic whitelist access\nfor DSP integration (OpenRTB ready)"),
    ("✅", "Entity Verification", "NPI-verified physicians, FDA-validated\ndrugs, verified institutions"),
    ("🏷️", "Multi-Taxonomy Mapping", "IAB 3.1, MeSH, ICD-10, DSM-5,\nRxNorm — all mapped"),
    ("🔄", "Ongoing Re-validation", "Scheduled re-scraping ensures\nURLs remain current & accurate"),
    ("📝", "Full Audit Trail", "Every classification decision is\ntraceable & explainable"),
]

for i, (icon, title, desc) in enumerate(deliverables):
    col = i % 4
    row = i // 4
    x = 0.8 + col * 3.05
    y = 1.4 + row * 2.8
    add_card(slide, x, y, 2.85, 2.4)
    add_text(slide, x + 0.15, y + 0.15, 2.6, 0.35, icon, font_size=28, alignment=PP_ALIGN.CENTER)
    add_text(slide, x + 0.15, y + 0.55, 2.6, 0.35, title, font_size=14, bold=True, color=ACCENT_BLUE, alignment=PP_ALIGN.CENTER)
    add_text(slide, x + 0.15, y + 1.0, 2.6, 1.2, desc, font_size=11, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# ============ SLIDE 7: ADMIN DASHBOARD ============
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, 1, 0.4, 11, 0.6, "Admin Dashboard", font_size=36, bold=True, color=WHITE)
add_accent_line(slide, 1, 1.0, 1.5)

pages = [
    ("Overview", "Total URLs, whitelist count,\nconfidence distribution,\nprocessing queue status,\nsystem health metrics"),
    ("Whitelist Explorer", "Searchable/filterable table,\nexport to CSV/XLSX,\nconfidence & category filters,\ninline URL preview"),
    ("HITL Review", "Low-confidence queue,\none-click approve/reject,\noverride with reason,\nreviewer performance"),
    ("Entity Browser", "Browse by: pharma, schools,\nphysicians, biotech,\ndevice manufacturers,\nmedical institutions"),
    ("Analytics", "Accuracy over time,\nClaude API cost tracking,\nprocessing speed metrics,\nexportable reports"),
    ("Settings", "Confidence thresholds,\nplatform management,\nre-scrape scheduling,\nAPI key management"),
]

for i, (title, desc) in enumerate(pages):
    col = i % 3
    row = i // 3
    x = 0.8 + col * 4
    y = 1.4 + row * 2.8
    add_card(slide, x, y, 3.7, 2.4)
    add_text(slide, x + 0.2, y + 0.15, 3.3, 0.35, title, font_size=17, bold=True, color=ACCENT_BLUE)
    sep = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x + 0.2), Inches(y + 0.55), Inches(2), Inches(0.02))
    sep.fill.solid()
    sep.fill.fore_color.rgb = ACCENT_BLUE
    sep.line.fill.background()
    add_text(slide, x + 0.2, y + 0.7, 3.3, 1.6, desc, font_size=13, color=LIGHT_GRAY)

add_text(slide, 1, 7.0, 11, 0.4, "Tech: Next.js on Cloudflare Pages ($0 hosting)  •  Auth via Supabase  •  Real-time updates via Supabase Realtime", font_size=13, color=MEDIUM_GRAY, alignment=PP_ALIGN.CENTER)

# ============ SLIDE 8: COST BREAKDOWN ============
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, 1, 0.4, 11, 0.6, "Monthly Infrastructure Costs", font_size=36, bold=True, color=WHITE)
add_accent_line(slide, 1, 1.0, 1.5)

# Three cost columns
scenarios = [
    ("Small Scale", "100K URLs", "$170–300/mo", ACCENT_BLUE, [
        ("Database (Supabase)", "$25"),
        ("AI (Claude API)", "$50–100"),
        ("Scraping (VPS)", "$20"),
        ("Redis / Queues", "$0"),
        ("API (CF Workers)", "$5"),
        ("Storage (R2)", "$0"),
        ("Monitoring", "$0"),
        ("Proxies", "$50–100"),
    ]),
    ("Medium Scale", "1M URLs", "$1,004–1,704/mo", ACCENT_GREEN, [
        ("Database (Supabase)", "$40"),
        ("AI (Claude API)", "$500–1,000"),
        ("Scraping (VPS)", "$80"),
        ("Redis / Queues", "$10"),
        ("API (CF Workers)", "$5"),
        ("Storage (R2)", "$5"),
        ("Monitoring", "$164"),
        ("Proxies", "$100–200"),
    ]),
    ("Large Scale", "50M URLs", "$12K–28K/mo", ORANGE, [
        ("Database (Supabase)", "$275–400"),
        ("AI (Claude API)", "$10.5K–25K"),
        ("Scraping (VPS)", "$200–500"),
        ("Redis / Queues", "$50–100"),
        ("API (CF Workers)", "$5–45"),
        ("Storage (R2)", "$15–75"),
        ("Monitoring", "$300–500"),
        ("Proxies", "$500–1K"),
    ]),
]

for i, (title, subtitle, total, color, items) in enumerate(scenarios):
    x = 0.8 + i * 4
    add_card(slide, x, 1.3, 3.7, 5.5)
    add_text(slide, x + 0.15, 1.4, 3.4, 0.35, title, font_size=20, bold=True, color=color, alignment=PP_ALIGN.CENTER)
    add_text(slide, x + 0.15, 1.8, 3.4, 0.3, subtitle, font_size=14, color=MEDIUM_GRAY, alignment=PP_ALIGN.CENTER)
    
    sep = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x + 0.4), Inches(2.15), Inches(2.9), Inches(0.02))
    sep.fill.solid()
    sep.fill.fore_color.rgb = color
    sep.line.fill.background()
    
    for j, (item, cost) in enumerate(items):
        y_pos = 2.35 + j * 0.35
        add_text(slide, x + 0.3, y_pos, 2.2, 0.3, item, font_size=11, color=LIGHT_GRAY)
        add_text(slide, x + 2.4, y_pos, 1.1, 0.3, cost, font_size=11, color=WHITE, alignment=PP_ALIGN.RIGHT)
    
    # Total
    sep2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x + 0.4), Inches(5.25), Inches(2.9), Inches(0.02))
    sep2.fill.solid()
    sep2.fill.fore_color.rgb = color
    sep2.line.fill.background()
    add_text(slide, x + 0.3, 5.4, 1.5, 0.35, "TOTAL", font_size=14, bold=True, color=color)
    add_text(slide, x + 1.8, 5.4, 1.6, 0.35, total, font_size=14, bold=True, color=WHITE, alignment=PP_ALIGN.RIGHT)

add_text(slide, 1, 7.0, 11, 0.4, "⚡ Claude API is the dominant cost. Batch processing & pre-filtering can reduce it 50–70%.", font_size=14, color=ORANGE, alignment=PP_ALIGN.CENTER)

# ============ SLIDE 9: TIMELINE ============
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, 1, 0.4, 11, 0.6, "Development Timeline & Milestones", font_size=36, bold=True, color=WHITE)
add_accent_line(slide, 1, 1.0, 1.5)

milestones = [
    ("M1", "Proof of Concept", "Week 4–5", "Working classifier on 3,000 PubMed URLs\nwith accuracy report", ACCENT_BLUE),
    ("M2", "Entity Resolution", "Week 8", "Drug, physician & org verification\nworking on test data", ACCENT_BLUE),
    ("M3", "First Whitelist", "Week 11", "100K URL whitelist delivered in\nCSV/XLSX format", ACCENT_GREEN),
    ("M4", "Admin Dashboard", "Week 14", "Dashboard with search, export,\nand HITL review system", ACCENT_GREEN),
    ("M5", "Production Launch", "Week 18–22", "Full system at target scale\nwith monitoring & documentation", ORANGE),
]

for i, (code, title, when, desc, color) in enumerate(milestones):
    y = 1.4 + i * 1.1
    # Timeline dot
    dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(1.5), Inches(y + 0.15), Inches(0.35), Inches(0.35))
    dot.fill.solid()
    dot.fill.fore_color.rgb = color
    dot.line.fill.background()
    tf = dot.text_frame
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    # Vertical line (except last)
    if i < 4:
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.65), Inches(y + 0.5), Inches(0.04), Inches(0.7))
        line.fill.solid()
        line.fill.fore_color.rgb = MEDIUM_GRAY
        line.line.fill.background()
    
    add_text(slide, 2.1, y + 0.05, 1.2, 0.35, code, font_size=16, bold=True, color=color)
    add_text(slide, 3.2, y + 0.05, 3, 0.35, title, font_size=16, bold=True, color=WHITE)
    add_text(slide, 6.5, y + 0.05, 1.5, 0.35, when, font_size=14, color=MEDIUM_GRAY)
    add_text(slide, 8.2, y, 4.5, 0.6, desc, font_size=12, color=LIGHT_GRAY)

add_card(slide, 1, 6.9, 11.2, 0.5)
add_text(slide, 1.3, 6.92, 10, 0.4, "Each milestone = client demo point — see progress, give feedback, confirm direction", font_size=14, color=ACCENT_GREEN, alignment=PP_ALIGN.CENTER)

# ============ SLIDE 10: CLOUDFLARE SERVICES ============
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, 1, 0.4, 11, 0.6, "Cloudflare Services — What We Use", font_size=36, bold=True, color=WHITE)
add_accent_line(slide, 1, 1.0, 1.5)

use_items = [
    ("Workers", "Whitelist API at edge", "$5/mo for 10M requests", "<20ms response time globally"),
    ("R2 Storage", "Document archival", "$0.015/GB, ZERO egress", "Perfect for raw HTML/PDF storage"),
    ("Hyperdrive", "PostgreSQL connection pooler", "Free on paid plan", "Pools connections to Supabase"),
    ("Pages", "Dashboard hosting", "$0", "Free static site hosting"),
]

dont_items = [
    ("Browser Rendering", "$2,430/mo at scale", "Lightpanda is 50x cheaper"),
    ("Workers AI", "No biomedical models", "Only sentiment analysis available"),
    ("D1 Database", "SQLite-based, max 5GB", "Cannot replace PostgreSQL + pgvector"),
    ("Vectorize", "$19,200/mo at 50M URLs", "pgvector is included free on Supabase"),
]

add_text(slide, 1, 1.3, 5, 0.4, "✅  USE", font_size=22, bold=True, color=ACCENT_GREEN)
for i, (name, desc, cost, note) in enumerate(use_items):
    y = 1.85 + i * 0.85
    add_card(slide, 1, y, 5.5, 0.75)
    add_text(slide, 1.2, y + 0.05, 1.5, 0.3, name, font_size=14, bold=True, color=ACCENT_GREEN)
    add_text(slide, 2.8, y + 0.05, 2, 0.3, desc, font_size=12, color=LIGHT_GRAY)
    add_text(slide, 1.2, y + 0.35, 2, 0.3, cost, font_size=11, color=ORANGE)
    add_text(slide, 3.5, y + 0.35, 2.8, 0.3, note, font_size=11, color=MEDIUM_GRAY)

add_text(slide, 7, 1.3, 5, 0.4, "❌  DON'T USE", font_size=22, bold=True, color=RED)
for i, (name, reason, alt) in enumerate(dont_items):
    y = 1.85 + i * 0.85
    add_card(slide, 6.8, y, 5.5, 0.75)
    add_text(slide, 7.0, y + 0.05, 1.8, 0.3, name, font_size=14, bold=True, color=RED)
    add_text(slide, 8.8, y + 0.05, 3.3, 0.3, reason, font_size=12, color=LIGHT_GRAY)
    add_text(slide, 7.0, y + 0.35, 5, 0.3, f"→ {alt}", font_size=11, color=MEDIUM_GRAY)

add_card(slide, 1, 5.5, 11.2, 1.0)
add_text(slide, 1.3, 5.6, 10, 0.4, "Fact-Checked Against Official Cloudflare Documentation (April 2026)", font_size=14, bold=True, color=ACCENT_BLUE)
add_text(slide, 1.3, 5.95, 10, 0.4, "Workers: $5/mo + $0.30/M requests  •  R2: $0.015/GB + $0 egress  •  Hyperdrive: Free PG pooling  •  Pages: Free hosting", font_size=12, color=LIGHT_GRAY)

# ============ SLIDE 11: OUTPUT FORMAT ============
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, 1, 0.4, 11, 0.6, "Output: Whitelist Format", font_size=36, bold=True, color=WHITE)
add_accent_line(slide, 1, 1.0, 1.5)

add_text(slide, 1, 1.3, 11, 0.4, "Excel-Compatible CSV/XLSX — Per RxNetwork Specification", font_size=20, bold=True, color=ACCENT_GREEN)

# Required columns table
columns = [
    ("url", "Deduplicated URL validated as HCP content"),
    ("source_domain", "Platform domain (scribd.com, slideshare.net, etc.)"),
    ("content_type", "PDF, PPT, white paper, clinical summary, research poster"),
    ("detected_medical_categories", "MeSH codes + IAB categories (semicolon-separated)"),
    ("detected_entity_associations", "Org names, physician names, drug names"),
    ("confidence_score", "Classification confidence (0.00–1.00)"),
]

add_card(slide, 1, 1.85, 11.2, 4.0)
add_text(slide, 1.3, 1.95, 10, 0.4, "Required Columns", font_size=16, bold=True, color=ACCENT_BLUE)

for i, (col, desc) in enumerate(columns):
    y = 2.45 + i * 0.5
    add_text(slide, 1.5, y, 3, 0.4, col, font_size=13, bold=True, color=ORANGE)
    add_text(slide, 4.8, y, 7, 0.4, desc, font_size=13, color=LIGHT_GRAY)

add_card(slide, 1, 6.1, 11.2, 1.2)
add_text(slide, 1.3, 6.2, 10, 0.4, "Extended Columns (Recommended)", font_size=16, bold=True, color=ACCENT_BLUE)
add_text(slide, 1.3, 6.6, 10, 0.5, "audience_type  •  source_type  •  iab_category_codes  •  icd10_codes  •  dsm5_categories  •  fda_drug_names  •  mesh_codes  •  last_validated_at", font_size=13, color=LIGHT_GRAY)

# ============ SLIDE 12: ENTITY CATEGORIES ============
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, 1, 0.4, 11, 0.6, "Target Entity Categories", font_size=36, bold=True, color=WHITE)
add_accent_line(slide, 1, 1.0, 1.5)

add_text(slide, 1, 1.2, 11, 0.4, "8 Entity Categories Per RxNetwork Specification", font_size=18, color=LIGHT_GRAY)

entities = [
    ("💊", "Pharmaceutical\nManufacturers", "FDA-verified pharma\ncompany identification"),
    ("🏫", "Medical Schools &\nAcademic Centers", "Accredited medical\neducation institutions"),
    ("🏛️", "Medical Trade\nAssociations", "AMA, specialty societies,\nprofessional organizations"),
    ("👨‍⚕️", "Recognized\nPhysicians", "NPI Registry verified,\nlicense-confirmed MDs"),
    ("👔", "Healthcare\nExecutives", "C-suite and leadership\nin healthcare orgs"),
    ("🧬", "Biotech\nCompanies", "Biotechnology firms,\nresearch companies"),
    ("🔬", "Medical Device\nManufacturers", "FDA-listed device\ncompanies"),
    ("🏥", "Prominent Medical\nInstitutions", "Major hospitals, research\ncenters, health systems"),
]

for i, (icon, title, desc) in enumerate(entities):
    col = i % 4
    row = i // 4
    x = 0.8 + col * 3.05
    y = 1.7 + row * 2.6
    add_card(slide, x, y, 2.85, 2.2)
    add_text(slide, x + 0.15, y + 0.15, 2.6, 0.4, icon, font_size=30, alignment=PP_ALIGN.CENTER)
    add_text(slide, x + 0.15, y + 0.6, 2.6, 0.5, title, font_size=13, bold=True, color=ACCENT_BLUE, alignment=PP_ALIGN.CENTER)
    add_text(slide, x + 0.15, y + 1.2, 2.6, 0.8, desc, font_size=11, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# ============ SLIDE 13: IMPORTANT NOTES ============
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, 1, 0.4, 11, 0.6, "Important Considerations", font_size=36, bold=True, color=WHITE)
add_accent_line(slide, 1, 1.0, 1.5)

notes = [
    ("Scribd/SlideShare Access", "Scribd has NO public API since 2017. Content access is limited to metadata scraping. Recommend as Phase 2 target — start with legally clean sources (PubMed, open-access journals) in Phase 1.", ORANGE),
    ("Classification Accuracy Ramp-Up", "Expect 85–90% accuracy initially, improving to 95%+ after human-in-the-loop feedback cycles. This is a 2–4 week tuning period after initial deployment.", ACCENT_BLUE),
    ("robots.txt Compliance", "We respect robots.txt on all platforms. Some sites (WebMD, etc.) may limit scraping rate. This is a legal requirement for sustainable operation.", ACCENT_GREEN),
    ("Ongoing Maintenance Required", "Medical content changes constantly — new drugs, new guidelines, new HCPs. Whitelists need periodic re-scraping and re-classification to stay current.", ACCENT_BLUE),
    ("Cost Scales with Volume", "At 100K URLs: ~$200/month infrastructure. At 50M URLs: ~$15K–20K/month (dominated by Claude API). Pre-filtering reduces this 50–70%.", ORANGE),
    ("Dev Cost vs Infrastructure Cost", "Development is a one-time cost. Infrastructure is monthly recurring. The quote should clearly separate these two components.", ACCENT_GREEN),
]

for i, (title, desc, color) in enumerate(notes):
    col = i % 2
    row = i // 2
    x = 0.8 + col * 6.1
    y = 1.3 + row * 1.95
    add_card(slide, x, y, 5.8, 1.7)
    add_text(slide, x + 0.2, y + 0.1, 5.4, 0.35, title, font_size=15, bold=True, color=color)
    add_text(slide, x + 0.2, y + 0.5, 5.4, 1.1, desc, font_size=12, color=LIGHT_GRAY)

# ============ SLIDE 14: NEXT STEPS ============
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_text(slide, 1, 0.4, 11, 0.6, "Next Steps", font_size=36, bold=True, color=WHITE)
add_accent_line(slide, 1, 1.0, 1.5)

add_card(slide, 1, 1.4, 5.5, 4.5)
add_text(slide, 1.3, 1.5, 5, 0.4, "Questions We Need Answered", font_size=20, bold=True, color=ACCENT_BLUE)
add_bullet_list(slide, 1.3, 2.0, 5, 3.5, [
    "How many URLs in the first batch?",
    "One-time batch or continuous system?",
    "Dashboard required or CSV-only?",
    "Who provides the seed URL list?",
    "Expected turnaround time?",
    "Which platforms are mandatory for Phase 1?",
    "Specific DSP integration needed?",
    "Budget range?",
], font_size=13)

add_card(slide, 6.8, 1.4, 5.5, 4.5)
add_text(slide, 7.1, 1.5, 5, 0.4, "Immediate Action Items", font_size=20, bold=True, color=ACCENT_GREEN)
add_bullet_list(slide, 7.1, 2.0, 5, 3.5, [
    "Confirm URL volume → finalizes cost quote",
    "Decide: batch processing vs SaaS product",
    "Confirm Phase 1 platform scope",
    "Agree on milestone-based delivery",
    "Sign-off on tech stack decisions",
    "Kick off Phase 0: Foundation",
    "Schedule weekly progress demos",
    "Begin 3,000-URL evaluation dataset",
], font_size=13)

add_card(slide, 1, 6.2, 11.2, 1.0)
add_text(slide, 1.3, 6.25, 10, 0.4, "Ready to Begin", font_size=20, bold=True, color=ORANGE)
add_text(slide, 1.3, 6.65, 10, 0.4, "Architecture is researched & documented  •  Tech stack is selected  •  Cost models are built  •  Waiting for client confirmation to start Phase 0", font_size=14, color=LIGHT_GRAY)

# ============ SAVE ============
output_path = r"c:\Users\akash\work\rxscope\RxScope_Client_Presentation.pptx"
prs.save(output_path)
print(f"Presentation saved to: {output_path}")
print(f"Total slides: {len(prs.slides)}")
