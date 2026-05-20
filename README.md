# Nigerian University MIS

Nigerian University Management Information System (UMIS) - A production-grade, multi-tenant, NDPA 2023-compliant university ERP serving Nigerian federal, state, and private universities.

## ⚠️ Phase 0 - Foundation Layer

This repository contains the **Phase 0 Foundation Layer** - the irreversible base upon which all subsequent phases build.

> **Warning**: A mistake in this phase requires dropping the entire database and starting over.

### What's Implemented

- ✅ Custom `User` model with 12 Nigerian university roles
- ✅ django-tenants multi-tenancy (schema-per-tenant)
- ✅ PostgreSQL with pgvector and pgAudit extensions
- ✅ JWT authentication with token refresh
- ✅ RBAC permissions for all 12 roles
- ✅ 7 Celery named queues
- ✅ Next.js 15 frontend scaffold
- ✅ Docker Compose for full stack development
- ✅ CI/CD pipeline (GitHub Actions)

### Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Django 5.1 + DRF + Django Ninja |
| Database | PostgreSQL 16 + pgvector |
| Async | Celery + Redis |
| Storage | MinIO (S3-compatible) |
| Frontend | Next.js 15 + TypeScript |
| Design | Tailwind CSS |

### Getting Started

1. **Clone the repository**
```bash
git clone https://github.com/your-org/university-mis.git
cd university_mis
```

2. **Set up environment**
```bash
cp .env.example .env
# Edit .env with your values
```

3. **Start with Docker**
```bash
cd infrastructure/docker
docker-compose up -d
```

4. **Run migrations**
```bash
python manage.py migrate
python manage.py createsuperuser
```

5. **Start development server**
```bash
python manage.py runserver
```

### Project Structure

```
university_mis/
├── config/              # Django configuration
│   ├── settings/       # Base, dev, staging, production
│   ├── urls.py
│   ├── asgi.py
│   └── celery.py
├── apps/               # Django applications
│   ├── core/          # Core models, middleware, tasks
│   ├── users/         # User models, auth, permissions
│   └── tenants/      # Multi-tenancy models
├── frontend/          # Next.js 15 application
├── infrastructure/    # Docker, K3s, Ansible
├── scripts/          # Management commands
└── tests/           # Unit, integration, e2e tests
```

### User Roles (12)

| Role | Description | 2FA Required |
|------|------------|--------------|
| student | Current student | No |
| lecturer | Academic staff | No |
| hod | Head of Department | No |
| dean | Faculty Dean | No |
| registrar | Registrar | Yes |
| bursar | Finance officer | Yes |
| vc | Vice-Chancellor | Yes |
| auditor | Internal Auditor | Yes |
| ict_admin | ICT Administrator | Yes |
| external_examiner | External examiner | No |
| alumni | Graduate | No |
| parent | Parent/Guardian | No |

### API Endpoints

| Endpoint | Description |
|---------|------------|
| `/api/v1/auth/login/` | JWT Login |
| `/api/v1/auth/logout/` | JWT Logout |
| `/api/v1/auth/refresh/` | Refresh Token |
| `/api/v1/users/me/` | Current User |
| `/health/` | Health Check (K3s) |
| `/metrics/` | Prometheus Metrics |

### Celery Queues

- `default` - General tasks
- `payments` - Finance tasks
- `jamb` - JAMB integration
- `notifications` - Email/SMS
- `documents` - Document processing
- `ml` - Machine learning
- `infra` - Infrastructure tasks

### Documentation

- [FLAGGED_GAPS.md](./docs/FLAGGED_GAPS.md) - Known deviations from Blueprint
- [RBAC Matrix](./docs/rbac_matrix.md) - Permission matrix (Phase 1)

### License

Proprietary - All rights reserved

### Credits

Built for Nigerian University System by University MIS Team