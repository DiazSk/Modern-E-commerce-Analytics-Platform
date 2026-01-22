# Modern E-Commerce Analytics Platform

A hands-on data engineering project demonstrating an end-to-end analytics pipeline, from data ingestion to business intelligence.

## 🚀 Project Overview

The goal of this project was to build a robust data platform that mimics a real-world scenario. I wanted to learn how to integrate industry-standard tools like **Apache Airflow**, **dbt**, and **AWS** to process e-commerce data and turn it into actionable insights.

**What I accomplished:**

- Built automated pipelines to ingest data from APIs, databases, and event streams.
- Designed a **Star Schema** data warehouse model.
- Managed cloud infrastructure (AWS S3) using **Terraform**.
- Ensured data quality with automated tests.
- Created dashboards to visualize sales and customer behavior.

---

## 🛠️ Tech Stack & Tools

I used this stack to understand how modern data teams build scalable platforms:

- **Languages:** Python, SQL
- **Infrastructure:** Terraform (IaC), Docker
- **Cloud Storage:** AWS S3 (Data Lake)
- **Orchestration:** Apache Airflow
- **Transformation:** dbt (Data Build Tool)
- **Warehouse:** PostgreSQL (Local)
- **Quality:** Great Expectations
- **Visualization:** Metabase

---

## 📊 Architecture

Here is the high-level design of the system I built:

![Architecture Diagram](docs/architecture/diagrams/high_level_architecture_diagram.png)

1.  **Ingest:** Airflow DAGs fetch data from a Mock API, a Postgres DB, and clickstream events.
2.  **Store:** Raw data is saved to an S3 Data Lake (managed by Terraform).
3.  **Transform:** dbt models clean and structure the data into a Star Schema (Fact & Dimensions).
4.  **Visualize:** Metabase connects to the final tables to show dashboards.

---

## 🏗️ Data Modeling

I implemented a **Dimensional Model** (Star Schema) to optimize for analytics:

- **Fact Table:** `fact_orders` (transactions).
- **Dimensions:** `dim_customers`, `dim_products`, `dim_date`.
- **Key Concept Implemented:** **SCD Type 2** for `dim_customers` to track history (e.g., when a customer changes segments).

![Dimensional Model](docs/architecture/diagrams/high_level_dimensional_model_diagram.png)

---

## 💡 Key Learnings & Features

### 1. Infrastructure as Code (Terraform)

Instead of clicking through the AWS console, I used Terraform to script the creation of S3 buckets and IAM policies. This taught me about state management and reproducible infrastructure.

### 2. Data Quality & Testing

I didn't just move data; I validated it.

- **dbt Tests:** 146 automated tests check for unique keys and null values.
- **Great Expectations:** Added a layer of validation on the source data.
- **Result:** Achieved a **96% pass rate** on data quality checks.

### 3. Workflow Orchestration

I wrote Python DAGs in Airflow to handle dependencies. For example, the transformation jobs only run after the ingestion jobs successfully complete.

### 4. Cost Optimization

I learned how to use S3 Lifecycle policies to automatically move old data to cheaper storage (Glacier), simulating how a company would save money on long-term retention.

---

## 📈 Dashboarding

I built dashboards to simulate answering business questions, such as "Who are our top customers?" or "Which product category sells best?".

- **Revenue Analysis:** Tracked sales trends over time.
- **Customer Segmentation:** Grouped customers by spending habits (Gold, Silver, Bronze).

---

## 🏃 Quick Start (Local Setup)

Want to run this locally? Here is how I set it up:

**Prerequisites:** Docker, Python 3.9+, AWS Account.

```bash
# 1. Clone the repo
git clone https://github.com/DiazSk/Modern-E-commerce-Analytics-Platform.git
cd Modern-E-commerce-Analytics-Platform

# 2. Setup Python Virtual Env
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure .env
cp .env.example .env
# (Add your AWS credentials in the file)

# 4. Provision Infrastructure
cd infrastructure
terraform init
terraform apply

# 5. Start Services
cd ..
docker-compose up -d
```

- **Airflow UI:** `http://localhost:8081` (admin/admin123)
- **Metabase UI:** `http://localhost:3001`

---

## 📂 Project Structure

```text
Modern-E-commerce-Analytics-Platform/
├── dags/                  # Airflow pipelines (Python)
├── transform/             # dbt project (SQL models & tests)
├── infrastructure/        # Terraform config (AWS resources)
├── docs/                  # Project documentation & diagrams
├── scripts/               # Helper scripts for setup/data gen
└── docker-compose.yml     # Container definition
```

---

## 📬 Contact

**Zaid Shaikh**

- **GitHub:** [@DiazSk](https://github.com/DiazSk)
- **LinkedIn:** [Zaid Shaikh](https://www.linkedin.com/in/zaidshaikhengineer/)
- **Email:** zaid07sk@gmail.com
