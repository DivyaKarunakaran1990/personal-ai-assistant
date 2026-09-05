from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import engine, SessionLocal
from models import Base,  Document
from services.memory_service import save_memory, get_memories
from ai.assistant import ask_ai
from fastapi.middleware.cors import CORSMiddleware
from services.pdf_service import save_pdf, extract_pdf_text

from prometheus_fastapi_instrumentator import Instrumentator

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Personal AI Assistant",
    description="AI-powered personal assistant with memory",
    version="1.0.0"
)

# OpenTelemetry tracing
trace.set_tracer_provider(TracerProvider())

otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4318/v1/traces"
)

span_processor = BatchSpanProcessor(otlp_exporter)

trace.get_tracer_provider().add_span_processor(span_processor)

FastAPIInstrumentor.instrument_app(app)

instrumentator = Instrumentator()
instrumentator.instrument(app)
instrumentator.expose(app, endpoint="/metrics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5174",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def root():
    return {
        "message": "Personal AI Assistant API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/memory")
def create_memory(
    category: str,
    content: str,
    db: Session = Depends(get_db)
):
    return save_memory(
        db,
        category,
        content
    )


@app.get("/memory")
def memories(
    db: Session = Depends(get_db)
):
    return get_memories(db)


@app.post("/chat")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):

    response = ask_ai(
        request.message,
        db
    )

    return {
        "message": request.message,
        "response": response
    } 

@app.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    content = await file.read()

    file_path = save_pdf(
        content,
        file.filename
    )

    text = extract_pdf_text(file_path)

    document = Document(
        filename=file.filename,
        content=text
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "id": document.id,
        "filename": document.filename,
        "message": "PDF uploaded and stored successfully.",
        "text_preview": text[:1000]
    }

@app.get("/test-document-search")
def test_document_search(
    query: str,
    db: Session = Depends(get_db)
):
    from services.document_service import search_documents

    return search_documents(db, query)