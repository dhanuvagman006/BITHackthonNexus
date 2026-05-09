# 3-Person Hackathon Task Split

For a hackathon, you should avoid trying to build a full enterprise backup platform.
Instead, build a **focused prototype** that demonstrates:

* Resilient backup architecture
* Secure isolated recovery
* Automated verification/testing
* Fast recovery orchestration

The best strategy is:

> Divide by system layers, not by features.

That prevents overlap and lets all 3 people work in parallel.

---

# Recommended Project Structure

Build a prototype with:

1. **Backup + Immutable Storage Layer**
2. **Recovery Orchestration + Dependency Engine**
3. **Monitoring + Security + Dashboard**

---

# Person 1 — Backup & Storage Engineer

## Responsibility

Build the **core backup pipeline** and protected storage architecture.

This person focuses on:

* Backup creation
* Versioning
* Integrity validation
* Immutable storage simulation

---

# Tasks

## 1. Automated Backup Service

Build:

* Scheduled backups
* Incremental backups
* Compression/encryption

Possible stack:

* Python
* Bash scripts
* rsync/restic/borgbackup

---

## 2. Immutable Backup Simulation

Implement:

* Write-once backup directory
* Version locking
* Read-only snapshots

Can simulate using:

* Linux file permissions
* Object storage mock
* MinIO/S3 versioning

---

## 3. Backup Verification

Critical feature.

Build:

* Hash verification
* Restore test verification
* Corruption detection

Example:

```bash
SHA256(file) == stored_hash
```

---

## 4. Multi-location Replication

Simulate:

* Local backup
* Offsite/cloud backup

Could use:

* Docker volumes
* Multiple folders/nodes

---

# Deliverables

* Backup engine
* Backup integrity checker
* Immutable storage demo
* Replication workflow

---

# Person 2 — Recovery & Orchestration Engineer

## Responsibility

Build the **recovery system**.

This is the most important demo component.

Focus on:

* Dependency mapping
* Recovery automation
* Restore sequencing
* Fast failover

---

# Tasks

## 1. Dependency Mapping Engine

Create dependency graph:

```text id="ysq4h6"
Database → Authentication → API → Frontend
```

Can use:

* JSON/YAML configs
* Graph structures

---

## 2. Automated Recovery Workflow

Build scripts that:

* Detect failure
* Restore systems in correct order
* Validate health checks

Possible tools:

* Python orchestration
* Docker Compose
* Kubernetes (optional)

---

## 3. Recovery Sandbox

Simulate:

* Clean recovery environment
* Isolated restore network

Very valuable for judging.

---

## 4. Recovery Time Optimization

Add:

* Parallel restores
* Priority-based recovery

Example:

| Priority | System         |
| -------- | -------------- |
| P1       | Authentication |
| P2       | Database       |
| P3       | Frontend       |

---

# Deliverables

* Recovery orchestrator
* Dependency-aware restore engine
* Sandbox recovery demo
* Recovery workflow scripts

---

# Person 3 — Security, Monitoring & Dashboard Engineer

## Responsibility

Build:

* Security controls
* Monitoring
* Visualization
* **Terminal-based Incident Dashboard** (No web browser)

This makes the project look polished, hacker-themed, and enterprise-grade.

---

# Tasks

## 1. Ransomware Attack Simulation

Simulate:

* File encryption attack
* Backup deletion attempts
* Lateral movement attempt

Can use safe mock scripts that show activity in the terminal.

---

## 2. Security Controls

Implement:

* Role-based access (CLI login)
* MFA mock (TOTP/SMS simulation in terminal)
* Backup isolation logic
* Alert generation (Terminal notifications/alerts)

---

## 3. Monitoring Dashboard

Build a **Terminal User Interface (TUI)** showing:

* Backup status (Live tables/progress bars)
* Integrity health (Status indicators)
* Recovery readiness
* Recovery time (Real-time timers)
* Threat alerts (Flashing alerts/banners)

Tech stack:

* **Python (Rich / Textual)** or **Node.js (Ink / Blessed)**
* Flask/FastAPI backend
* Logging & Alerting system

---

## 4. Incident Visualization

Add:

* **Terminal Timeline** of attack (Scrollable log/events)
* Recovery progress (ASCII progress bars)
* System status (Dynamic terminal panels)

This dramatically improves presentation quality during a live demo.

---

# Deliverables

* Security module
* **Terminal Monitoring Dashboard**
* Attack simulation scripts
* CLI Alerting system

---

# Shared Architecture

```text id="xjlwmq"
                +-------------------+
                | Terminal Dashboard|
                | Security Console  |
                +---------+---------+
                          |
          +---------------+--------------+
          |                              |
+---------v---------+        +-----------v----------+
| Backup Engine     |        | Recovery Orchestrator|
| Immutable Storage |        | Dependency Manager   |
+---------+---------+        +-----------+----------+
          |                              |
          +--------------+---------------+
                         |
               +---------v---------+
               | Recovery Sandbox  |
               | Clean Restore Env |
               +-------------------+
```

---

# Suggested Tech Stack

| Component     | Recommended        |
| ------------- | ------------------ |
| Backend       | Python + FastAPI   |
| Frontend / TUI| Python (Rich/Textual)|
| Backup Engine | Restic/Borg/rclone |
| Storage       | MinIO/S3           |
| Containers    | Docker             |
| Database      | PostgreSQL         |
| Monitoring    | Prometheus/Grafana |
| Orchestration | Python scripts     |

---

# Best Hackathon Strategy

Do NOT try to build:

* Real enterprise-scale infrastructure
* Full cloud integration
* Production-grade DR systems

Instead focus on:

## What judges care about

### 1. Clear problem understanding

Explain WHY backups fail during ransomware.

---

### 2. Strong architecture

Show:

* Immutable backups
* Isolated recovery
* Automated validation

---

### 3. Realistic attack simulation

This is a huge differentiator.

---

### 4. Live recovery demo

Best possible demo flow:

```text id="wjm1ws"
1. Simulate ransomware attack
2. Systems fail
3. Dashboard detects compromise
4. Recovery orchestrator activates
5. Clean backups restored
6. Services recover automatically
7. Recovery metrics displayed
```

That will impress judges far more than complex code.

---

# Final Recommendation

## Split by ownership

| Person   | Focus                      |
| -------- | -------------------------- |
| Person 1 | Backup + Immutable Storage |
| Person 2 | Recovery Orchestration     |
| Person 3 | Security + Dashboard       |

This minimizes dependency conflicts and maximizes parallel development.

The key to winning is not building the biggest system.

It’s demonstrating:

* realistic ransomware failure,
* intelligent recovery,
* and operational resilience under pressure.
