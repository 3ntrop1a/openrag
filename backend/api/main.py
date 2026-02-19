"""
OpenRAG API Gateway
Main entry point for all user requests
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import List, Optional
import httpx
import os
import psycopg2
import psycopg2.extras
from loguru import logger
import uuid
from datetime import datetime, timedelta
from prometheus_fastapi_instrumentator import Instrumentator
from jose import JWTError, jwt
from passlib.context import CryptContext

# ─── Configuration ─────────────────────────────────────────────────────────────
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:8001")
API_VERSION = "1.0.0"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"host={os.getenv('POSTGRES_HOST','postgres')} "
    f"port={os.getenv('POSTGRES_PORT','5432')} "
    f"dbname={os.getenv('POSTGRES_DB','openrag_db')} "
    f"user={os.getenv('POSTGRES_USER','openrag')} "
    f"password={os.getenv('POSTGRES_PASSWORD','openrag123')}"
)

JWT_SECRET  = os.getenv("JWT_SECRET_KEY", "openrag-change-me-in-production-please")
JWT_ALG     = "HS256"
JWT_EXPIRE  = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours

pwd_ctx       = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ─── FastAPI init ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="OpenRAG API",
    description="API Gateway pour la solution RAG",
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── DB helpers ────────────────────────────────────────────────────────────────

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    try:
        yield conn
    finally:
        conn.close()

# ─── Auth helpers ───────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    credentials_exc = HTTPException(status_code=401, detail="Invalid or expired token",
                                    headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT id, username, role, is_active FROM users WHERE username = %s", (username,))
        user = cur.fetchone()

    if not user or not user["is_active"]:
        raise credentials_exc
    return dict(user)

async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# ─── Startup: seed default admin ───────────────────────────────────────────────

@app.on_event("startup")
async def seed_default_admin():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
            count = cur.fetchone()[0]
            if count == 0:
                cur.execute(
                    "INSERT INTO users (username, hashed_password, role) VALUES (%s, %s, %s)",
                    ("admin", hash_password("admin"), "admin")
                )
                logger.info("Default admin user created (admin/admin)")
            else:
                logger.info("Admin user already exists, skipping seed")
        conn.close()
    except Exception as e:
        logger.error(f"Failed to seed admin user: {e}")

# ─── Auth Pydantic models ───────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str

class UserOut(BaseModel):
    id: str
    username: str
    role: str
    is_active: bool
    created_at: str

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4)
    role: str = Field("user", pattern="^(admin|user)$")

# ─── Auth Routes ───────────────────────────────────────────────────────────────

@app.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
async def login(form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    """Authenticate and receive a JWT access token."""
    with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT id, username, hashed_password, role, is_active FROM users WHERE username = %s",
            (form.username,)
        )
        user = cur.fetchone()

    if not user or not user["is_active"] or not verify_password(form.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_token({"sub": user["username"], "role": user["role"]})
    return TokenResponse(access_token=token, username=user["username"], role=user["role"])

@app.get("/auth/me", tags=["Auth"])
async def me(current_user: dict = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return {"username": current_user["username"], "role": current_user["role"]}

@app.get("/auth/users", tags=["Auth"])
async def list_users(db=Depends(get_db), _=Depends(require_admin)):
    """List all users. Admin only."""
    with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT id, username, role, is_active, created_at FROM users ORDER BY created_at DESC")
        rows = cur.fetchall()
    return {"users": [
        {**dict(r), "id": str(r["id"]), "created_at": r["created_at"].isoformat()}
        for r in rows
    ]}

@app.post("/auth/users", response_model=UserOut, tags=["Auth"])
async def create_user(body: UserCreate, db=Depends(get_db), _=Depends(require_admin)):
    """Create a new user. Admin only."""
    with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT id FROM users WHERE username = %s", (body.username,))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail="Username already taken")
        cur.execute(
            "INSERT INTO users (username, hashed_password, role) VALUES (%s, %s, %s) "
            "RETURNING id, username, role, is_active, created_at",
            (body.username, hash_password(body.password), body.role)
        )
        row = dict(cur.fetchone())
    return UserOut(**{**row, "id": str(row["id"]), "created_at": row["created_at"].isoformat()})

@app.delete("/auth/users/{user_id}", tags=["Auth"])
async def delete_user(user_id: str, db=Depends(get_db), current=Depends(require_admin)):
    """Delete a user. Admin only. Cannot delete yourself."""
    with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    if row["username"] == current["username"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    with db.cursor() as cur:
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    return {"deleted": user_id}

@app.patch("/auth/users/{user_id}/password", tags=["Auth"])
async def change_password(user_id: str, body: dict, db=Depends(get_db), _=Depends(require_admin)):
    """Change a user's password. Admin only."""
    new_password = body.get("password", "")
    if len(new_password) < 4:
        raise HTTPException(status_code=422, detail="Password must be at least 4 characters")
    with db.cursor() as cur:
        cur.execute("UPDATE users SET hashed_password = %s WHERE id = %s",
                    (hash_password(new_password), user_id))
    return {"status": "updated"}

# ============================================
# Existing Models
# ============================================

class QueryRequest(BaseModel):
    """Requête de recherche/question"""
    query: str = Field(..., description="Question ou requête de l'utilisateur")
    collection_id: Optional[str] = Field(None, description="ID de la collection à interroger")
    max_results: int = Field(5, description="Nombre maximum de résultats", ge=1, le=20)
    use_llm: bool = Field(True, description="Utiliser le LLM pour générer une réponse")
    metadata_filter: Optional[dict] = Field(None, description="Filtres de métadonnées")

class QueryResponse(BaseModel):
    """Réponse à une requête"""
    query_id: str
    answer: Optional[str] = None
    sources: List[dict] = []
    execution_time_ms: int
    timestamp: str

class DocumentUploadResponse(BaseModel):
    """Réponse après upload de document"""
    document_id: str
    filename: str
    status: str
    message: str

class HealthResponse(BaseModel):
    """Statut de santé de l'API"""
    status: str
    version: str
    timestamp: str
    services: dict

# ============================================
# Routes
# ============================================

@app.get("/", tags=["General"])
async def root():
    """Point d'entrée racine"""
    return {
        "service": "OpenRAG API Gateway",
        "version": API_VERSION,
        "status": "operational",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Vérification de santé de l'API et des services"""
    services = {}
    
    # Check orchestrator
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/health")
            services["orchestrator"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        services["orchestrator"] = "unreachable"
        logger.error(f"Orchestrator health check failed: {e}")
    
    return HealthResponse(
        status="healthy",
        version=API_VERSION,
        timestamp=datetime.utcnow().isoformat(),
        services=services
    )

@app.post("/query", response_model=QueryResponse, tags=["RAG"])
async def process_query(request: QueryRequest):
    """
    Traiter une requête utilisateur
    
    Cette endpoint :
    1. Recherche les documents pertinents
    2. Génère une réponse avec le LLM (si activé)
    3. Retourne la réponse et les sources
    """
    query_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    try:
        # Timeout augmenté pour permettre la génération LLM (peut prendre 30-120s)
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{ORCHESTRATOR_URL}/process-query",
                json={
                    "query_id": query_id,
                    "query": request.query,
                    "collection_id": request.collection_id,
                    "max_results": request.max_results,
                    "use_llm": request.use_llm,
                    "metadata_filter": request.metadata_filter
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Orchestrator error: {response.text}"
                )
            
            result = response.json()
            
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return QueryResponse(
            query_id=query_id,
            answer=result.get("answer"),
            sources=result.get("sources", []),
            execution_time_ms=execution_time,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Query timeout")
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/upload", response_model=DocumentUploadResponse, tags=["Documents"])
async def upload_document(
    file: UploadFile = File(...),
    collection_id: Optional[str] = None
):
    """
    Upload un document pour indexation
    
    Formats supportés : PDF, DOCX, TXT, MD, etc.
    """
    document_id = str(uuid.uuid4())
    
    try:
        # Lire le contenu du fichier
        content = await file.read()
        
        # Envoyer à l'orchestrateur
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": (file.filename, content, file.content_type)}
            data = {
                "document_id": document_id,
                "collection_id": collection_id or "default"
            }
            
            response = await client.post(
                f"{ORCHESTRATOR_URL}/documents/ingest",
                files=files,
                data=data
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Upload failed: {response.text}"
                )
            
            result = response.json()
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            status="processing",
            message="Document uploaded successfully and is being processed"
        )
        
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", tags=["Documents"])
async def list_documents(
    collection_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Liste tous les documents"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "collection_id": collection_id,
                "status": status,
                "limit": limit,
                "offset": offset
            }
            response = await client.get(
                f"{ORCHESTRATOR_URL}/documents",
                params={k: v for k, v in params.items() if v is not None}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch documents"
                )
            
            return response.json()
            
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}", tags=["Documents"])
async def get_document(document_id: str):
    """Récupère les détails d'un document"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/documents/{document_id}")
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Document not found")
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch document"
                )
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}", tags=["Documents"])
async def delete_document(document_id: str):
    """Supprime un document"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(f"{ORCHESTRATOR_URL}/documents/{document_id}")
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Document not found")
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to delete document"
                )
            
            return {"status": "deleted", "document_id": document_id}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collections", tags=["Collections"])
async def list_collections():
    """Liste toutes les collections"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/collections")
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch collections"
                )
            
            return response.json()
            
    except Exception as e:
        logger.error(f"List collections error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
