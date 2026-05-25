# LLM Data Assistant

Ask questions about your business data in plain English. Get accurate, grounded answers powered by a local LLM and a Cube.js semantic layer — no cloud, no API keys, no SQL hallucinations.

---

## How It Works

```
User Question (natural language)
        |
        v
phi3 LLM (Ollama)
  "Convert this question to a Cube.js JSON query"
        |
        v
Cube.js Semantic Layer
  Validates query, generates SQL, queries PostgreSQL
        |
        v
phi3 LLM (Ollama)
  "Convert this raw data into a plain English answer"
        |
        v
Answer displayed in Streamlit chat UI
```

The LLM **never writes raw SQL**. It only generates a small JSON object using measure and dimension names defined in the Cube.js schema. This eliminates SQL hallucinations — the LLM cannot invent column names or table names that don't exist in the semantic layer.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Docker Compose                    │
│                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐  │
│  │Streamlit │───▶│ chain.py │───▶│    Ollama    │  │
│  │  :8501   │    │LangChain │◀───│  phi3 :11434 │  │
│  └──────────┘    └────┬─────┘    └──────────────┘  │
│                       │                             │
│                  ┌────▼─────┐                       │
│                  │  Cube.js │                       │
│                  │  :4000   │                       │
│                  └────┬─────┘                       │
│                       │                             │
│                  ┌────▼─────┐                       │
│                  │Postgres18│                       │
│                  │  :5433   │                       │
│                  └──────────┘                       │
└─────────────────────────────────────────────────────┘
```

## Stack

| Component | Technology | Purpose |
|---|---|---|
| Database | PostgreSQL 18 | Northwind business dataset |
| Semantic Layer | Cube.js 1.6 | Defines business metrics, prevents SQL hallucinations |
| LLM Backend | Ollama + phi3 | Natural language → Cube.js JSON, data → answer |
| Orchestration | Python + LangChain | Chains LLM calls and Cube.js API calls |
| UI | Streamlit | Chat interface |
| Infrastructure | Docker Compose | Local deployment, zero cloud |

---

## Dataset — Northwind

Classic business dataset with 6 tables:

| Table | Rows | Description |
|---|---|---|
| customers | 50 | Company names, cities, countries |
| employees | 9 | Staff with titles, departments, salaries |
| products | 50 | Products with categories and prices |
| categories | 8 | Product categories |
| orders | 61 | Orders with ship country and freight |
| order_details | 77 | Line items with price, quantity, discount |

---

## Cube.js Schema (Semantic Layer)

4 cubes defined in `cubejs/schema/`:

**Orders** — joins `orders` + `order_details`
- Measures: `totalRevenue`, `orderCount`, `avgOrderValue`, `totalFreight`
- Dimensions: `shipCountry`, `orderDate`, `customerId`

**Products** — joins `products` + `categories`
- Measures: `avgPrice`, `totalStock`, `outOfStockCount`
- Dimensions: `productName`, `category`, `unitPrice`

**Customers**
- Measures: `count`
- Dimensions: `companyName`, `city`, `country`

**Employees** — uses window functions for salary ranking
- Measures: `avgSalary`, `maxSalary`, `totalPayroll`
- Dimensions: `fullName`, `department`, `salary`, `salaryRank`

---

## Prerequisites

- Docker + Docker Compose
- Git

That's it. No Python, no Node.js, no Ollama needed on the host machine — everything runs in containers.

---

## Setup & Run

### 1. Clone the repo

```bash
git clone https://github.com/Susmit07/llm-data-assistant.git
cd llm-data-assistant
```

### 2. Start PostgreSQL (separate container, not in compose)

```bash
docker run -d \
  --name northwind-db \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_DB=northwind \
  -p 5433:5432 \
  --health-cmd="pg_isready -U admin -d northwind" \
  --health-interval=10s \
  --health-timeout=5s \
  --health-retries=5 \
  postgres:18beta1
```

### 3. Load the Northwind schema and seed data

```bash
docker exec -i northwind-db psql -U admin -d northwind < postgres/init.sql
```

Verify:
```bash
docker exec northwind-db psql -U admin -d northwind -c "\dt"
```

### 4. Start Cube.js and Ollama

```bash
docker compose up -d cubejs ollama
```

### 5. Pull the phi3 model into Ollama

This downloads ~2.2GB — do this once:

```bash
docker exec semantic-layer-ollama-1 ollama pull phi3
```

Wait for it to finish:
```bash
docker exec semantic-layer-ollama-1 ollama list
```

### 6. Verify Cube.js loaded the schema

```bash
curl -s http://localhost:4000/cubejs-api/v1/meta \
  -H "Authorization: Bearer dev-secret" | python3 -m json.tool
```

You should see 4 cubes: Orders, Products, Customers, Employees.

### 7. Start the Streamlit app

```bash
docker compose up -d app
```

### 8. Open the UI

```
http://localhost:8501
```

---

## Test Queries

Verify the REST API works before using the UI:

**Top 5 countries by revenue:**
```bash
curl -s -X POST http://localhost:4000/cubejs-api/v1/load \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-secret" \
  -d '{"query": {"measures": ["Orders.totalRevenue"], "dimensions": ["Orders.shipCountry"], "order": {"Orders.totalRevenue": "desc"}, "limit": 5}}'
```

**Highest paid employee per department:**
```bash
curl -s -X POST http://localhost:4000/cubejs-api/v1/load \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-secret" \
  -d '{"query": {"dimensions": ["Employees.fullName", "Employees.department", "Employees.salary", "Employees.salaryRank"], "filters": [{"member": "Employees.salaryRank", "operator": "equals", "values": ["1"]}], "order": {"Employees.salary": "desc"}}}'
```

---

## Sample Questions for the UI

- What are the top 5 countries by total revenue?
- How many orders do we have in total?
- Which product category has the highest average price?
- How many customers do we have per country?
- Who is the highest paid employee per department?
- Which products are out of stock?
- What is the total freight cost by country?

---

## Project Structure

```
llm-data-assistant/
├── docker-compose.yml          # Cube.js + Ollama + Streamlit app
├── .gitignore
├── README.md
├── postgres/
│   └── init.sql                # Northwind schema + seed data
├── cubejs/
│   ├── cube.js                 # Cube.js config
│   └── schema/
│       ├── Orders.js           # Orders + order_details cube
│       ├── Products.js         # Products + categories cube
│       ├── Customers.js        # Customers cube
│       └── Employees.js        # Employees cube with window functions
└── app/
    ├── app.py                  # Streamlit chat UI
    ├── chain.py                # LangChain orchestration (NL → Cube JSON → NL)
    ├── cubejs_client.py        # HTTP client for Cube.js REST API
    └── requirements.txt
```

---

## Key Design Decisions

**Why Cube.js instead of direct SQL generation?**
LLMs hallucinate SQL — wrong column names, wrong joins, wrong aggregations. Cube.js acts as a validated contract. The LLM only generates a small JSON with measure/dimension names we explicitly provided. Cube.js owns all SQL generation internally.

**Why phi3 over Llama-3?**
phi3 at 3.8B parameters is faster for structured JSON generation tasks and uses less memory. Llama-3-8B gives better reasoning on ambiguous questions but is slower on CPU. Swap by changing `OLLAMA_MODEL` in `docker-compose.yml`.

**Why local LLM?**
Zero data egress, no API cost, no rate limits, fully reproducible. Works offline.

**Why window functions in the base SQL?**
Cube.js doesn't support window functions in measure definitions. By computing `RANK() OVER (...)` in the cube's base `sql` query, we expose the result as a dimension that can be filtered on — enabling "highest paid per department" queries without any application-level post-processing.

---

## Extending the Schema

Adding a new data source:
1. Create a new file in `cubejs/schema/` (e.g. `Suppliers.js`)
2. Define the cube with measures and dimensions
3. Cube.js hot-reloads in dev mode — no restart needed
4. Add the new cube's fields to the `CUBE_SCHEMA` string in `app/chain.py`

No changes needed to the LLM layer, the UI, or the infrastructure.

---

## Stopping Everything

```bash
docker compose down
docker stop northwind-db && docker rm northwind-db
```
