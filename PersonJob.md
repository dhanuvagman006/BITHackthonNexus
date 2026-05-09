# Team Structure (3 Members)

---

# Member 1 — Backend + Infrastructure Lead

## Responsibilities
Build and manage:

- Backup APIs
- MinIO object storage
- Dockerized services
- Recovery endpoints
- PostgreSQL integration

## Tech Stack

- Go *(recommended for performance)* or FastAPI
- PostgreSQL
- MinIO
- Docker

## Deliverables

### Core APIs
- Backup upload API
- Backup retrieval API
- Restore API
- Recovery trigger endpoint

### Infrastructure
- Immutable backup storage
- Docker Compose setup
- Persistent PostgreSQL integration

### Expected Outcome
A reliable backend capable of securely storing, restoring, and managing backups during ransomware recovery scenarios.

---

# Member 2 — Security + Recovery Logic Lead

## Responsibilities
Build and manage:

- Ransomware attack simulator
- Checksum validation system
- Dependency graph engine
- Restore sequencing logic

## Tech Stack

- Python
- FastAPI
- NetworkX

## Deliverables

### Security Components
- Encrypted-file ransomware simulation
- Backup integrity verification
- SHA256 checksum validation

### Recovery Logic
- Dependency mapping engine
- Recovery order calculation
- Automated restore sequencing

### Expected Outcome
A smart recovery engine capable of validating backups and restoring systems in the correct dependency order.

---

# Member 3 — Frontend + Demo + AI Lead

## Responsibilities
Build and manage:

- Monitoring dashboard
- Attack visualization
- Recovery progress UI
- Demo and pitch flow
- Optional AI assistant integration

## Tech Stack

- Next.js
- Tailwind CSS
- shadcn/ui
- Recharts

## Deliverables

### Frontend Features
- Operational dashboard
- Attack animation visualization
- Recovery progress tracking
- System metrics screen

### Demo Features
- End-to-end recovery flow presentation
- Interactive ransomware simulation
- AI-powered assistant *(optional)*

### Expected Outcome
A polished and interactive frontend that clearly demonstrates ransomware attacks, backup recovery, and system restoration workflows.

---

# Overall Project Goal

Develop a ransomware recovery and backup orchestration platform that can:

- Simulate ransomware attacks
- Validate backup integrity
- Store immutable backups
- Recover systems intelligently
- Visualize recovery operations in real time

---

# Suggested Workflow

1. Member 2 simulates ransomware attack
2. Member 1 stores immutable backups
3. Member 2 validates backup integrity
4. Member 2 generates dependency-aware restore order
5. Member 1 triggers recovery APIs
6. Member 3 visualizes attack and recovery process

---

# Final Architecture Overview

## Backend Layer
- FastAPI/Go services
- PostgreSQL database
- MinIO object storage

## Security Layer
- Encryption simulator
- Checksum validator
- Dependency graph engine

## Frontend Layer
- Dashboard UI
- Attack monitoring
- Recovery visualization
- Demo presentation flow

---

# Optional Future Enhancements

- AI-powered recovery recommendations
- Kubernetes deployment
- Multi-node backup replication
- Real-time alerting system
- Role-based access control (RBAC)
- Disaster recovery analytics