# 🛡️ RetailGuard — Fraud Detection & Prevention Suite

A full-stack, open-source fraud detection platform for retail transactions.  
Built with **FastAPI + MongoDB + scikit-learn** backend and a **Vue.js** frontend.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **ML Fraud Scoring** | Isolation Forest model scores every transaction 0–100% risk |
| ⚡ **Real-Time Alerts** | Flags high-risk transactions instantly with email notifications |
| 📁 **CSV / JSON Upload** | Bulk upload transaction files for batch analysis |
| 📊 **Risk Dashboards** | Charts for volume trends, risk distribution, top merchants |
| 🕵️ **Investigation Cases** | Collaborative workflow with comments, assignment, status tracking |
| 🔐 **RBAC** | Three roles: Admin, Analyst, Investigator |
| 📋 **Audit Logging** | Every system action is logged immutably |
| 🐳 **Docker Ready** | Full stack via a single `docker-compose up` |

---

## 🚀 Quick Start

### Option A — Docker (recommended)

```bash
# 1. Clone and start
git clone https://github.com/your-org/retailguard.git
cd retailguard
docker-compose up -d

# 2. Seed demo data (first run)
docker-compose --profile seed run seed

# 3. Open the app
# Frontend  →  http://localhost:5173
# API docs  →  http://localhost:8000/docs
```

### Option B — Local Development

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Start MongoDB locally first, then:
uvicorn main:app --reload --port 8000

# Seed demo data
python seed.py
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## 🔑 Demo Credentials

| Role | Email | Password |
|---|---|---|
| Admin | `admin@retailguard.io` | `Admin@123` |
| Analyst | `analyst@retailguard.io` | `Analyst@123` |
| Investigator | `investigator@retailguard.io` | `Invest@123` |

---

## 📂 Project Structure

```
retailguard/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings via env vars
│   ├── database.py          # MongoDB connection
│   ├── seed.py              # Demo data seeder
│   ├── ml/
│   │   └── detector.py      # IsolationForest fraud scorer
│   ├── models/
│   │   └── schemas.py       # Pydantic models for all entities
│   ├── routes/
│   │   ├── auth.py          # Login, register, /me
│   │   ├── transactions.py  # Upload, list, score
│   │   ├── alerts.py        # Alert management
│   │   ├── cases.py         # Investigation cases + comments
│   │   ├── users.py         # User management (admin)
│   │   └── dashboard.py     # Stats, audit logs
│   └── services/
│       ├── auth.py          # JWT + RBAC middleware
│       ├── audit.py         # Audit log writer
│       └── notifications.py # Email alerts (SMTP)
│
├── frontend/
│   └── src/
│       ├── views/
│       │   ├── LoginView.vue
│       │   ├── DashboardView.vue
│       │   ├── TransactionsView.vue
│       │   ├── UploadView.vue
│       │   ├── AlertsView.vue
│       │   ├── CasesView.vue
│       │   ├── CaseDetailView.vue
│       │   ├── UsersView.vue
│       │   └── AuditView.vue
│       ├── components/      # RiskBar, StatusBadge, ToastContainer
│       ├── store/           # Pinia auth store
│       ├── router/          # Vue Router with auth guards
│       └── utils/           # Axios API client, toast service
│
├── docker-compose.yml
├── sample_transactions.csv  # Test upload file
└── sample_transactions.json
```

---

## 🧠 ML Engine

The fraud detector uses **Isolation Forest** from scikit-learn:

- Trained on synthetic baseline data on first run (bootstrapped model)
- Scores each transaction from `0.0` (safe) to `1.0` (high fraud risk)
- Business rule boosts applied for: foreign cards, odd-hour transactions, high frequency, large amounts, distant locations
- Default fraud threshold: **0.70** (configurable via `FRAUD_THRESHOLD` env var)
- Model persisted to `/tmp/retailguard_model.pkl` and reloaded on restart

---

## 🔌 API Reference

Full interactive docs at **http://localhost:8000/docs** (Swagger UI)

Key endpoints:

```
POST   /api/auth/login            Login
POST   /api/auth/register         Register new user

POST   /api/transactions/upload   Upload CSV/JSON file
GET    /api/transactions          List transactions (filterable)
GET    /api/transactions/summary  Aggregate counts

GET    /api/alerts                List alerts
PATCH  /api/alerts/{id}          Update alert status

POST   /api/cases                 Create investigation case
GET    /api/cases                 List cases
PATCH  /api/cases/{id}           Update case
POST   /api/cases/{id}/comments  Add comment

GET    /api/dashboard             Dashboard statistics
GET    /api/audit-logs            Audit log (admin only)
```

---

## ⚙️ Configuration

| Variable | Default | Description |
|---|---|---|
| `MONGO_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `SECRET_KEY` | *(must set)* | JWT signing key |
| `FRAUD_THRESHOLD` | `0.7` | Risk score cutoff for flagging |
| `SMTP_HOST` | — | SMTP server for email alerts |
| `SMTP_USER` | — | SMTP username |
| `SMTP_PASSWORD` | — | SMTP password |
| `ALERT_EMAIL` | — | Recipient for fraud alert emails |

---

## 📄 License

MIT — free to use, modify, and distribute.
