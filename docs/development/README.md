# Development Documentation

**Developer Setup and Testing Guides**

---

## 🛠️ Developer Environment Setup

### Prerequisites

**Required:**
- Docker Desktop
- Git
- Python 3.9+
- AWS Account (free tier)

**Optional:**
- VS Code with extensions
- DBeaver or pgAdmin
- Postman (for API testing)

---

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/DiazSk/Modern-E-commerce-Analytics-Platform.git
cd Modern-E-commerce-Analytics-Platform
```

### 2. Setup Environment Variables
```bash
# Copy example env file
cp .env.example .env

# Edit with your credentials
# Required: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Initialize Database
```bash
# Generate sample data
python scripts/generate_data.py

# Load into PostgreSQL
python scripts/load_data.py
```

### 5. Run dbt Models
```bash
cd transform
dbt run
dbt test
```

### 6. Access UIs
- **Airflow:** http://localhost:8081 (admin/admin123)
- **Metabase:** http://localhost:3001
- **pgAdmin:** http://localhost:5050

---

## 📁 Project Structure

```
Modern-E-commerce-Analytics-Platform/
├── dags/                    # Airflow DAG definitions
│   ├── ingest_api_products.py
│   ├── ingest_postgres_orders.py
│   └── ingest_clickstream_events.py
├── transform/               # dbt project
│   ├── models/
│   │   ├── staging/         # Cleaning & standardization
│   │   └── marts/           # Business logic
│   ├── tests/
│   └── dbt_project.yml
├── scripts/                 # Utility scripts
│   ├── generate_data.py     # Create sample data
│   ├── load_data.py         # Load to PostgreSQL
│   └── setup_airflow_connections.py
├── infrastructure/          # Terraform IaC
├── docs/                    # Documentation
├── docker-compose.yml       # Service orchestration
└── requirements.txt         # Python dependencies
```

---

## 🧪 Testing

### Data Quality Tests

**dbt Tests:**
```bash
cd transform

# Run all tests
dbt test

# Test specific model
dbt test --select dim_customers

# Test with detailed output
dbt test --store-failures
```

**Great Expectations:**
```bash
# Run checkpoint
python scripts/run_checkpoint.py

# View results
open gx/uncommitted/data_docs/local_site/index.html
```

### Unit Tests
```bash
# Run Python tests
pytest tests/

# With coverage
pytest --cov=scripts tests/
```

---

## 🔄 Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# ... edit files ...

# Test locally
dbt run --select your_model
dbt test --select your_model

# Commit with semantic message
git commit -m "feat: add customer segmentation model"

# Push to remote
git push origin feature/your-feature-name
```

### 2. Code Review

- Create pull request
- Ensure tests pass
- Request review from team
- Address feedback

### 3. Merge to Main

```bash
# Merge via PR
# Then update local
git checkout develop
git pull origin develop
```

---

## 📝 Coding Standards

### Python
- Follow PEP 8
- Use type hints
- Add docstrings
- Maximum line length: 100 characters

### SQL
- Use lowercase keywords
- Snake_case for identifiers
- CTEs for complex logic
- Comments for business logic

### dbt
- One model per file
- Models in appropriate folders (staging/, marts/)
- Always add tests (unique, not_null, relationships)
- Document in schema.yml

---

## 🐛 Debugging

### Airflow DAG Issues

**Check Logs:**
```bash
docker logs airflow-scheduler
docker exec airflow-scheduler airflow dags list
```

**Test DAG Syntax:**
```bash
python dags/your_dag.py
```

### dbt Model Issues

**Compile Query:**
```bash
dbt compile --select your_model
# Check target/compiled/
```

**Run with Debug:**
```bash
dbt run --select your_model --debug
```

### Database Connection Issues

**Test Connection:**
```bash
docker exec postgres-warehouse psql -U warehouse_user -d warehouse -c "SELECT 1"
```

---

## 📚 Additional Resources

### Data Generation
See [data-generation.md](./data-generation.md) for:
- Synthetic data creation
- Data volume configuration
- Loading procedures

### Project Demonstration
See [demo-guide.md](./demo-guide.md) for:
- 5-minute demo script
- Key talking points
- Interview preparation

### Learning Resources
- [dbt Learn](https://courses.getdbt.com/)
- [Airflow Documentation](https://airflow.apache.org/docs/)
- [Great Expectations Tutorial](https://docs.greatexpectations.io/)

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request
5. Wait for review

---

**Last Updated:** November 10, 2025
**Environment:** Local Docker Compose
**Python Version:** 3.11
