# AI Website Builder Agent

A professional, full-stack multi-agent system that translates natural language business descriptions into fully planned, coded, previewable, and production-deployable business websites.

Built with **FastAPI**, **SQLite (SQLAlchemy Async)**, **Google Gemini AI**, **Git Checkpointing**, and **React + Tailwind CSS + TypeScript**.

---

## 🏗️ Multi-Agent Architecture

The system coordinates **5 specialized AI agents** matching the engineering workflow:

```
[ User Describes Business ]
          │
          ▼
┌───────────────────────────────────────────────┐
│  1. Orchestrator Agent                        │
│     - Formulates structured WebsitePlan       │
│     - Defines sections, theme & layout specs  │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│  2. Asset Agent                               │
│     - Sources verified Unsplash photography   │
│     - Generates vector SVG brand logo mark    │
│     - Curates Lucide icon sets & SVG fallbacks│
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│  3. Design Agent                              │
│     - Codes responsive semantic HTML5         │
│     - Implements modern Tailwind CSS styles   │
│     - Creates mobile menu drawer & animations │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│  4. Backend Agent                             │
│     - Implements contact form handler script  │
│     - Adds anti-bot honeypot validation       │
│     - Emits standalone serverless functions   │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│  5. Verification & Security Gate              │
│     - Orchestrator: Does everything match plan│
│     - Execution Agent: Asks command approval  │
│     - Git: Saves atomic version checkpoint    │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│  6. Live Preview & Interactive Iteration      │
│     - Responsive viewports (Desktop/Tablet/Mob)│
│     - Forms submit live to project database   │
│     - User reviews & requests natural changes │
└──────────────────────┬────────────────────────┘
                       │ (When user ready to publish)
                       ▼
┌───────────────────────────────────────────────┐
│  7. Execution Agent: Deployment Approval      │
│     - Validates build output                  │
│     - Deploys to Local / Netlify / Vercel     │
│     - Returns verified live published URL     │
└───────────────────────────────────────────────┘
```

---

## 🌟 Key Features

1. **Autonomous Multi-Agent Workflow**: Five specialized agents coordinate via structured Pydantic schemas.
2. **Real Source Code Generation**: Actual `index.html`, `styles.css`, `main.js`, and `netlify/functions/` files written to isolated project workspaces (`storage/projects/<project_id>/`).
3. **Genuine Contact Form Submissions**: Contact forms on generated websites submit to the backend API (`POST /api/v1/projects/<id>/contact`) and persist in SQLite. Never fakes success.
4. **Git Checkpointing & Safe Rollback**: Every milestone and natural language change creates an atomic Git commit with rollback capability.
5. **Security Command Sandbox**:
   - Strict allowlisted commands (`npm run build`, `npm test`, `git status`, etc.).
   - Explicit user authorization modal before executing terminal commands.
   - Comprehensive path traversal protections.
6. **Live Multi-Device Preview**: Instant responsive preview (Desktop 100%, Tablet 768px, Mobile 375px) in an isolated sandbox iframe.
7. **Natural Language Refinements**: Users type requested changes (e.g. *"Change color scheme to emerald, update headline to X"*), and the Orchestrator applies surgical fixes.
8. **Real Deployments**: Deploy to Local High-Performance Static Server, Netlify Deploy API, or Vercel Deployments API with verified live URLs.
9. **Google Gemini Integration**: Native support for `gemini-2.5-flash`, `gemini-1.5-pro`, and `gemini-1.5-flash` with zero-config deterministic fallback when testing without a key.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Node.js 18+ (Tested on Node.js v24.19.0 / npm 11.17.0)
- Git (Installed & accessible in PATH)

### 1. Environment Setup

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configure your **Google Gemini API Key** (optional - system includes deterministic fallback):
```env
GEMINI_API_KEY="AIzaSy..."
GEMINI_MODEL="gemini-2.5-flash"
```

### 2. Backend Setup & Startup

Run the backend server on port 8000:
```bash
python run.py
```
*The database and tables are created automatically on first run.*
- API documentation available at: `http://127.0.0.1:8000/docs`
- Health check available at: `http://127.0.0.1:8000/api/v1/health`

### 3. Frontend Setup & Startup

In a separate terminal:
```bash
cd frontend
npm.cmd install
npm.cmd run dev
```
Open your browser at `http://localhost:5173`.

---

## 🧪 Running Automated Tests

Run the backend automated test suite:
```bash
python -m pytest backend/tests/test_backend.py -v
```

Tests verify:
- Complete 5-agent pipeline execution
- Live contact submission persistence
- Git checkpointing and rollback
- Directory traversal prevention
- Command allowlist enforcement
- Deployment readiness checks

---

## 🔒 Security Architecture

- **Path Confinement**: All file reads/writes are strictly constrained inside `storage/projects/<project_id>/`.
- **Command Allowlisting**: Only vetted commands can run; arbitrary commands and destructive flags are blocked.
- **Approval Gate**: Commands and deployments require explicit user confirmation.
- **Secret Isolation**: Server API keys and provider tokens are never sent to the browser or embedded in generated source code.
