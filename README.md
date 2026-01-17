# urWallet Backend

A production-ready FastAPI backend for personal expense tracking with AI-powered insights.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | **FastAPI** with async support |
| Database | **PostgreSQL** via SQLAlchemy async |
| Auth | **Firebase Authentication** |
| AI | **Groq** (LLaMA 3.3 70B) |
| Container | **Docker** + Docker Compose |

## Architecture

```
backend/
├── app/
│   ├── main.py              # Application entry point
│   ├── dependencies.py      # Auth & common dependencies
│   ├── core/
│   │   ├── config.py        # Environment settings
│   │   ├── database.py      # PostgreSQL connection
│   │   └── firebase.py      # Firebase Admin SDK
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── user.py
│   │   └── transaction.py
│   ├── schemas/             # Pydantic request/response schemas
│   │   ├── user.py
│   │   └── transaction.py
│   ├── routers/             # API route handlers
│   │   ├── auth.py          # GET /api/auth/me
│   │   ├── user.py          # PUT /api/user/settings
│   │   ├── transactions.py  # CRUD /api/transactions
│   │   ├── dashboard.py     # GET /api/dashboard/summary
│   │   └── ai.py            # AI insights & categorization
│   └── services/
│       └── ai.py            # Groq AI business logic
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Quick Start

### Prerequisites

- **Docker** & **Docker Compose**
- **Firebase project** with Authentication enabled
- **Groq API key** (optional, for AI features)

### 1. Setup Environment

```bash
cd backend

# Copy environment template
cp .env.example .env

# Edit .env with your values
```

### 2. Firebase Credentials

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Project Settings → Service Accounts → Generate New Private Key
3. Save as `firebase-credentials.json` in the `backend/` directory

### 3. Run with Docker

```bash
# Start PostgreSQL and backend
docker-compose up --build -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend

# Stop
docker-compose down
```

The API will be available at `http://localhost:8000`

## Local Development

### Without Docker

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup PostgreSQL locally and update DATABASE_URL in .env

# Run the server
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

### Authentication (Firebase)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/me` | Get current user (creates on first login) |

### User
| Method | Endpoint | Description |
|--------|----------|-------------|
| PUT | `/api/user/settings` | Update user preferences |

### Transactions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/transactions` | List all transactions |
| POST | `/api/transactions` | Create transaction |
| PUT | `/api/transactions/{id}` | Update transaction |
| DELETE | `/api/transactions/{id}` | Delete transaction |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/summary` | Monthly summary (query: month, year) |

### AI Features
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ai/insights` | Monthly AI insights (query: month, year) |
| POST | `/api/ai/categorize` | AI category suggestion |
| GET | `/api/ai/spike-detection` | Spending spike warnings |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `FIREBASE_CREDENTIALS_PATH` | Path to Firebase JSON | `firebase-credentials.json` |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | `*` |
| `GROQ_API_KEY` | Groq API key for AI features | Optional |
| `DEBUG` | Enable debug logging | `false` |

## Authentication Flow

1. **Frontend** handles login/registration via Firebase JS SDK
2. **Frontend** sends Firebase ID token in `Authorization: Bearer <token>` header
3. **Backend** verifies token using Firebase Admin SDK
4. **Backend** creates user in PostgreSQL on first login

## Database

Tables are auto-created on startup. For production, consider using Alembic migrations:

```bash
# Initialize Alembic (one-time)
alembic init alembic

# Generate migration
alembic revision --autogenerate -m "Initial"

# Apply migrations
alembic upgrade head
```

## Testing

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

## Deployment Considerations

1. **Secrets**: Use environment variables or secret management (AWS Secrets Manager, etc.)
2. **HTTPS**: Always use HTTPS in production
3. **Database**: Use managed PostgreSQL (RDS, Cloud SQL, Supabase)
4. **Scaling**: Uvicorn with multiple workers or behind Gunicorn
5. **Monitoring**: Add health checks, logging aggregation

---

**API Documentation**: `http://localhost:8000/docs` (Swagger UI)
