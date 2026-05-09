phoenixvault/
│
├── frontend/                 # Next.js dashboard
│
├── backend/
│   ├── api/                  # Main APIs
│   ├── recovery-engine/      # Recovery logic
│   ├── verifier/             # Backup verification
│   └── simulator/            # Ransomware simulator
│
├── storage/
│   └── backups/              # Local backup mount
│
├── infra/
│   ├── docker/
│   └── kubernetes/           # Optional
│
├── scripts/
│   ├── attack.sh
│   ├── restore.sh
│   └── verify.py
│
├── docker-compose.yml
│
└── README.md