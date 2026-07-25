from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sqlite3
import pandas as pd
from datetime import datetime
import os

# Fix path - go up one level if nested
if "n100-financial-intelligence" in os.getcwd() and os.getcwd().endswith("n100-financial-intelligence"):
    DB_PATH = "db/nifty100.db"
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "../../db/nifty100.db")

app = FastAPI(
    title="N100 Financial Intelligence Platform",
    description="API for Nifty 100 company analytics",
    version="1.0.0"
)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def root():
    return {"name": "N100 Financial Intelligence", "version": "1.0.0", "docs": "/docs"}

@app.get("/api/v1/health")
def health_check():
    try:
        conn = get_db()
        stats = pd.read_sql(
            "SELECT COUNT(*) as companies FROM companies",
            conn
        )
        conn.close()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": {"companies": stats.iloc[0]['companies']}
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/v1/companies")
def list_companies():
    conn = get_db()
    companies = pd.read_sql("SELECT id, company_name FROM companies LIMIT 20", conn)
    conn.close()
    return {"count": len(companies), "companies": companies.to_dict('records')}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)