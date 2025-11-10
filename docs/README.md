# Documentation

**Modern E-Commerce Analytics Platform**

Production-grade data engineering platform for end-to-end analytics.

---

## 📂 Documentation Structure

### [Architecture](./architecture/)
System design, data flow, and architectural decisions.
- **[Diagrams](./architecture/diagrams/)** - PlantUML architecture and data model diagrams
- **[Decisions](./architecture/decisions/)** - Architecture Decision Records (ADRs)

### [Operations](./operations/)
Operational runbooks and data ingestion procedures.
- **[Runbooks](./operations/runbooks/)** - Setup and operational procedures
- **[Data Ingestion](./operations/data-ingestion/)** - DAG-specific pipeline guides

### [Data Catalog](./data-catalog/)
Data dictionary, schema documentation, and lineage.
- **[Data Dictionary](./data-catalog/data-dictionary.md)** - Complete schema reference

### [Analytics](./analytics/)
Business intelligence setup and dashboard documentation.
- **[Metabase](./analytics/metabase/)** - BI dashboard guides and SQL queries

### [Development](./development/)
Developer setup and testing guides.

---

## 🚀 Quick Links

**Getting Started:**
1. [Airflow Setup](./operations/runbooks/airflow-setup.md)
2. [Data Ingestion Overview](./operations/data-ingestion/)
3. [Data Dictionary](./data-catalog/data-dictionary.md)

**Architecture:**
- [Technology Stack](./architecture/decisions/001-technology-stack.md)
- [Partitioning Strategy](./architecture/decisions/002-partitioning-strategy.md)
- [Architecture Diagrams](./architecture/diagrams/)

**Analytics:**
- [Metabase Setup](./analytics/metabase/)
- [SQL Query Library](./analytics/metabase/METABASE_ULTIMATE_GUIDE.md#complete-sql-library)

---

## 📝 Documentation Standards

### File Naming
- Use lowercase with hyphens: `file-name.md`
- ADRs: `XXX-decision-title.md` (e.g., `001-technology-stack.md`)

### Structure
- One H1 header per document
- Table of contents for docs > 200 lines
- Code blocks with language tags
- Links are relative paths

### Maintenance
- Update timestamp on each change
- Version major documentation changes
- Keep archive for historical reference

---

**Last Updated:** November 10, 2025
**Maintained By:** Data Engineering Team
