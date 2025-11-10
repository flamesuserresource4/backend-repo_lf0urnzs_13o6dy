import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from database import create_document, get_documents

app = FastAPI(title="Divine Flavours Bakery API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateCakeOrder(BaseModel):
    size: str
    description: str
    image_base64: str
    customer_name: str | None = None
    contact: str | None = None


@app.get("/")
def read_root():
    return {"message": "Divine Flavours API is running"}


@app.post("/api/cakes", status_code=201)
def create_cake(order: CreateCakeOrder):
    # Validate size values
    allowed = {"small_1_layer", "big_1_layer", "multi_layer"}
    if order.size not in allowed:
        raise HTTPException(status_code=400, detail="Invalid size")

    # Persist to DB
    inserted_id = create_document("cakeorder", order.dict())
    return {"id": inserted_id}


@app.get("/api/cakes")
def list_cakes(limit: int | None = 50):
    docs = get_documents("cakeorder", {}, limit or 50)

    # Convert ObjectId to string if present
    result = []
    for d in docs:
        d["id"] = str(d.get("_id"))
        d.pop("_id", None)
        result.append(d)
    return {"items": result}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
