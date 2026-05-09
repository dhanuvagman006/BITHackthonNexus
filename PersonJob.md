# 🛡️ IronVault — Ransomware Backup & Recovery Platform

> A ransomware recovery and backup orchestration platform that detects attacks early, protects backups from compromise, and recovers everything automatically — fast.

---

## 🔥 Full Feature Flow

```
USER OPENS APP
      ↓
📊 DASHBOARD
• Recovery Readiness Score (0-100%)
• Backup health overview (healthy / corrupted / outdated)
• Active alerts & system status
• Live metrics across all systems
      ↓
🔍 GAP ANALYSIS
• Reliability score
• Recovery Planning score
• Infrastructure Security score
• Operational Readiness score
      ↓
💾 BACKUP MANAGER
• All backups listed with status
• SHA256 hash verified ✅
• Encrypted at rest ✅
• 3-2-1-1 storage locations (local / offsite / air-gapped / immutable)
      ↓
🚨 ATTACK DETECTION
• Real-time file entropy monitoring
• Canary file tripwires
• Large data transfer alerts (double extortion detection)
• Auto-isolate infected system instantly
      ↓
⚡ RECOVERY ORCHESTRATOR
• Auto-finds last clean, verified backup
• Dependency-based restore order
• Recovery time estimate
• One-click recovery trigger
      ↓
📋 RUNBOOK GENERATOR
• Auto-generated plain-English staff instructions
• Checklist format — nothing missed
• System-specific steps based on what was attacked
      ↓
🧪 FIRE DRILL SYSTEM
• Simulate fake ransomware attack
• Test if recovery actually works
• Updates Readiness Score after each drill
      ↓
📈 POST ATTACK REPORT
• Full attack timeline
• Systems affected & data at risk
• Time to recover
• Recommendations to prevent next time
```

---

## 👥 Team Structure (3 Members)

---

### Member 1 — Backend + Infrastructure Lead

**Responsibilities:** Build and manage core APIs, storage, and infrastructure

**Tech Stack:** FastAPI or Go · PostgreSQL · MinIO · Docker

#### Deliverables

**Core APIs**
- Backup upload API
- Backup retrieval API
- Restore API
- Recovery trigger endpoint

**Infrastructure**
- Immutable backup storage (WORM policy)
- Air-gapped storage simulation
- Docker Compose setup
- Persistent PostgreSQL integration

**Expected Outcome:** A reliable backend capable of securely storing, restoring, and managing backups during ransomware recovery scenarios.

---

### Member 2 — Security + Recovery Logic Lead

**Responsibilities:** Build ransomware simulation, integrity validation, and smart recovery engine

**Tech Stack:** Python · FastAPI · NetworkX

#### Deliverables

**Security Components**
- Ransomware attack simulator (file encryption simulation)
- Canary file tripwire system
- SHA256 checksum validation
- Backup integrity verification
- Data encryption at rest (stolen data = useless)

**Recovery Logic**
- Dependency mapping engine
- Recovery order calculation (DB → App → Web → Workstations)
- Automated restore sequencing
- Clean backup selector (finds last uncompromised backup)

**Expected Outcome:** A smart recovery engine that validates backups, detects attacks early, and restores systems in the correct dependency order.

---

### Member 3 — Frontend + Demo + AI Lead

**Responsibilities:** Build the full UI, demo flow, and AI-powered features

**Tech Stack:** Next.js · Tailwind CSS · shadcn/ui · Recharts · D3.js

#### Deliverables

**Frontend Features**
- 📊 Dashboard with Recovery Readiness Score
- 🔍 Gap Analysis screen (4 scored categories)
- 💾 Backup Manager with status indicators
- 🚨 Live attack detection & alert screen
- ⚡ Recovery Orchestrator UI with dependency map
- 📋 Auto-generated Runbook viewer
- 🧪 Fire Drill simulator
- 📈 Post Attack Report screen

**Demo Features**
- End-to-end recovery flow presentation
- Live attack simulation with one button
- Before vs After comparison (old system vs IronVault)
- AI-powered runbook assistant (Claude API)

**Expected Outcome:** A polished, interactive frontend that tells the complete story — attack happens, system responds, recovery completes.

---

## 🔄 Suggested Workflow

```
1. Member 2 simulates ransomware attack
2. Member 2 detects via canary files + entropy monitoring
3. Member 1 auto-isolates infected system
4. Member 2 validates backup integrity (SHA256)
5. Member 2 generates dependency-aware restore order
6. Member 1 triggers recovery APIs with clean backup
7. Member 3 visualizes attack detection + recovery in real time
8. Member 3 generates runbook for staff
9. Member 3 shows Post Attack Report to judges
```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────┐
│                FRONTEND LAYER               │
│  Dashboard · Gap Analysis · Attack Monitor  │
│  Recovery UI · Runbook · Fire Drill · Report│
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│               SECURITY LAYER                │
│  Canary Files · Entropy Detection           │
│  SHA256 Validator · Dependency Graph        │
│  Ransomware Simulator · Encryption at Rest  │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│               BACKEND LAYER                 │
│  FastAPI/Go Services · PostgreSQL           │
│  MinIO Object Storage · Docker Compose      │
│  Immutable Storage · Air-gapped Backup      │
└─────────────────────────────────────────────┘
```

---

## 🎯 Overall Project Goal

Develop a ransomware recovery and backup orchestration platform that can:

- 🔍 Detect ransomware attacks in real time
- 🔒 Protect backups from direct compromise (air-gapped + immutable)
- 🔐 Encrypt all data at rest (stolen data = useless to attacker)
- ✅ Validate backup integrity before every restore
- 📦 Store immutable backups using 3-2-1-1 rule
- ⚡ Recover systems intelligently in correct dependency order
- 📋 Guide staff with auto-generated runbooks
- 📊 Visualize recovery operations in real time
- 🧪 Test recovery readiness with automated fire drills

---

## 🚀 Demo Flow for Judges (5 Minutes)

```
Step 1 → Open Dashboard — show Readiness Score: 34% (before)
Step 2 → Show Gap Analysis — "here's why the old system failed"
Step 3 → Press "Simulate Attack" — canary files trigger alert
Step 4 → Watch auto-isolation + recovery start automatically
Step 5 → Recovery completes — Readiness Score: 94%
Step 6 → Show auto-generated Staff Runbook
Step 7 → Show Post Attack Report — full timeline + proof
```

---

## 🔮 Future Enhancements

- AI-powered recovery recommendations
- Kubernetes deployment
- Multi-node backup replication
- Real-time alerting system
- Role-based access control (RBAC)
- Disaster recovery analytics
- Cost calculator (downtime cost vs IronVault cost)