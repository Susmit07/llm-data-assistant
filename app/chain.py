import json
import re
import requests
import os
from cubejs_client import run_cube_query

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3")

CUBE_SCHEMA = """
Available cubes and their fields:

Orders:
  measures:   Orders.count, Orders.orderCount, Orders.totalRevenue, Orders.avgOrderValue, Orders.totalFreight
  dimensions: Orders.shipCountry, Orders.orderDate, Orders.customerId, Orders.employeeId

Products:
  measures:   Products.count, Products.avgPrice, Products.totalStock, Products.outOfStockCount
  dimensions: Products.productName, Products.category, Products.unitPrice

Customers:
  measures:   Customers.count
  dimensions: Customers.companyName, Customers.city, Customers.country

Employees:
  measures:   Employees.count, Employees.avgSalary, Employees.maxSalary, Employees.totalPayroll
  dimensions: Employees.fullName, Employees.title, Employees.department, Employees.salary, Employees.salaryRank
"""

NL_TO_CUBE_PROMPT = """You are a Cube.js query generator.

{schema}

Rules:
- Always prefix measure and dimension names with the cube name (e.g. Orders.totalRevenue not totalRevenue)
- "order" must be an object like {{"Orders.totalRevenue": "desc"}}
- Each filter must have exactly these keys: "member", "operator", "values" (values must be an array of strings)
- Valid operators: equals, notEquals, contains, gt, gte, lt, lte, set, notSet
- Return ONLY valid JSON, no markdown, no explanation, no code blocks
- Valid keys: measures, dimensions, filters, order, limit

Example without filters:
Question: What are the top 5 countries by total revenue?
Answer:
{{
  "measures": ["Orders.totalRevenue"],
  "dimensions": ["Orders.shipCountry"],
  "order": {{"Orders.totalRevenue": "desc"}},
  "limit": 5
}}

Example with filters:
Question: Who is the highest paid employee per department?
Answer:
{{
  "dimensions": ["Employees.fullName", "Employees.department", "Employees.salary", "Employees.salaryRank"],
  "filters": [{{"member": "Employees.salaryRank", "operator": "equals", "values": ["1"]}}],
  "order": {{"Employees.salary": "desc"}}
}}

Question: {question}
Answer:
"""

METRIC_TO_NL_PROMPT = """Answer the question based on the data below in 1-2 clear sentences.

Question: {question}
Data: {data}

Answer:
"""

def _call_ollama(prompt: str) -> str:
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120
    )
    response.raise_for_status()
    return response.json()["response"].strip()

def _extract_json(text: str) -> dict:
    # strip markdown code blocks if present
    text = re.sub(r"```(?:json)?", "", text).strip()
    # find first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in LLM output: {text}")
    query = json.loads(match.group())
    # Cube.js requires limit to be an int, LLM sometimes returns a string
    if query.get("limit") is not None:
        query["limit"] = int(query["limit"])
    else:
        query.pop("limit", None)
    # filters must be an array of valid Cube.js filter objects
    if "filters" in query:
        if not isinstance(query["filters"], list):
            query.pop("filters", None)
        else:
            valid_filters = []
            for f in query["filters"]:
                if isinstance(f, dict) and "member" in f and "operator" in f and "values" in f:
                    if not isinstance(f["values"], list):
                        f["values"] = [str(f["values"])]
                    valid_filters.append(f)
            if valid_filters:
                query["filters"] = valid_filters
            else:
                query.pop("filters", None)
    return query

DATA_KEYWORDS = [
    "revenue", "sales", "order", "orders", "product", "products",
    "customer", "customers", "employee", "employees", "country",
    "category", "price", "stock", "freight", "salary", "department",
    "top", "highest", "lowest", "total", "average", "count", "how many",
    "which", "what is", "show me", "list"
]

def _is_data_question(question: str) -> bool:
    q = question.lower()
    return any(kw in q for kw in DATA_KEYWORDS)

def generate_cube_query(question: str) -> dict:
    """Step 1 only: NL -> Cube.js JSON. Returns the query for user review."""
    prompt = NL_TO_CUBE_PROMPT.format(schema=CUBE_SCHEMA, question=question)
    raw_output = _call_ollama(prompt)

    try:
        cube_query = _extract_json(raw_output)
    except (ValueError, json.JSONDecodeError):
        retry_prompt = prompt + "\nIMPORTANT: Return ONLY the JSON object, nothing else."
        raw_output = _call_ollama(retry_prompt)
        try:
            cube_query = _extract_json(raw_output)
        except (ValueError, json.JSONDecodeError) as e:
            return {"error": f"LLM did not return valid JSON: {str(e)}", "raw": raw_output}

    return {"cube_query": cube_query}


def execute_and_answer(question: str, cube_query: dict) -> dict:
    """Step 2+3: Execute confirmed query against Cube.js, return NL answer."""
    try:
        cube_result = run_cube_query(cube_query)
    except requests.HTTPError as e:
        return {"error": f"Cube.js query failed: {e.response.text}", "cube_query": cube_query}

    if not cube_result:
        return {"answer": "No data found for that question.", "cube_query": cube_query, "raw_data": []}

    prompt2 = METRIC_TO_NL_PROMPT.format(
        question=question,
        data=json.dumps(cube_result[:10])
    )
    answer = _call_ollama(prompt2)

    return {
        "answer": answer,
        "cube_query": cube_query,
        "raw_data": cube_result
    }
