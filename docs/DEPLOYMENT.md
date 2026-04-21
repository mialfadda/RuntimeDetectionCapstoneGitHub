# Deployment Guide — Runtime Detection Capstone

## Prerequisites
- Docker and Docker Compose installed
- Git installed
- Cloud provider account (AWS/GCP/Azure)

---

## Local Development Setup

### 1. Clone the repository
git clone https://github.com/mialfadda/RuntimeDetectionCapstoneGitHub.git
cd RuntimeDetectionCapstoneGitHub

### 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate
.venv\Scripts\activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Set up environment variables
cp .env.example .env

### 5. Initialize database
flask --app run.py db upgrade

### 6. Run the app
python run.py

---

## Docker Deployment

### 1. Build and run all services
docker-compose up --build

### 2. Run in background
docker-compose up -d

### 3. Check logs
docker-compose logs -f web

### 4. Stop all services
docker-compose down

---

## Production Deployment

### Environment Variables Required
| Variable | Description |
|---|---|
| DATABASE_URL | PostgreSQL connection string |
| REDIS_URL | Redis connection string |
| SECRET_KEY | Flask secret key |
| JWT_SECRET_KEY | JWT signing key |
| PRIMARY_MODEL_PATH | Path to ML model files |

### Health Checks
- GET /health — quick health check
- GET /health/detailed — checks DB and Redis
- GET /metrics — Prometheus metrics

### Auto-scaling Rules
- Scale up when CPU above 70%
- Scale up when memory above 80%
- Minimum 2 instances always running
- Maximum 10 instances

### Database Backups
- Automated daily backups at 2AM UTC
- Backups retained for 30 days
- Point-in-time recovery enabled

### Load Balancer
- Health check endpoint: /health
- Health check interval: 30 seconds
- Unhealthy threshold: 3 failed checks

---

## CI/CD Pipeline

Every push to master automatically:
1. Runs all tests
2. Runs linter
3. Builds Docker image
4. Deploys if all checks pass

---

## Rollback Procedure

If deployment fails revert the commit:
git revert HEAD
git push origin master

To roll back model version run in Python:
from app.models.model_manager import rollback_model
rollback_model(model_id=1)