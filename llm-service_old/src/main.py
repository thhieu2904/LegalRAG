"""
LLM Service - Local Gemma/Llama model
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

from .config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global model and tokenizer
model = None
tokenizer = None


# ============= MODELS =============

class GenerateRequest(BaseModel):
    """Generation request"""
    prompt: str
    max_length: int = settings.MAX_LENGTH
    temperature: float = settings.TEMPERATURE
    top_p: float = settings.TOP_P


class GenerateResponse(BaseModel):
    """Generation response"""
    success: bool
    text: str
    prompt_tokens: int
    completion_tokens: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    device: str


# ============= APP =============

app = FastAPI(
    title="LLM Service",
    description="Text generation using local Gemma/Llama models",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Load model on startup"""
    global model, tokenizer
    
    logger.info(f"🚀 Loading LLM model: {settings.MODEL_NAME}")
    logger.warning("⏳ This may take a few minutes (downloading model)...")
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            settings.MODEL_NAME,
            cache_dir=settings.MODEL_CACHE_DIR
        )
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            settings.MODEL_NAME,
            cache_dir=settings.MODEL_CACHE_DIR,
            device_map="auto",
            torch_dtype=torch.float16 if settings.DEVICE == "cuda" else torch.float32
        )
        
        logger.info(f"✅ Model loaded: {settings.MODEL_NAME}")
        logger.info(f"✅ LLM Service started on {settings.DEVICE}")
    
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    global model, tokenizer
    if model:
        del model
    if tokenizer:
        del tokenizer
    logger.info("✅ LLM Service stopped")


# ============= ENDPOINTS =============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check"""
    return HealthResponse(
        status="healthy" if model and tokenizer else "unhealthy",
        model_loaded=model is not None and tokenizer is not None,
        device=settings.DEVICE
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate text using LLM"""
    try:
        if model is None or tokenizer is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        # Tokenize
        inputs = tokenizer(request.prompt, return_tensors="pt").to(settings.DEVICE)
        input_length = inputs["input_ids"].shape[1]
        
        # Generate
        outputs = model.generate(
            **inputs,
            max_length=request.max_length,
            temperature=request.temperature,
            top_p=request.top_p,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        
        # Decode
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the generated part
        generated_only = generated_text[len(request.prompt):]
        
        return GenerateResponse(
            success=True,
            text=generated_only,
            prompt_tokens=input_length,
            completion_tokens=outputs[0].shape[0] - input_length
        )
    
    except Exception as e:
        logger.error(f"❌ Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "llm-service",
        "model": settings.MODEL_NAME,
        "device": settings.DEVICE,
        "max_length": settings.MAX_LENGTH,
        "endpoints": {
            "health": "/health",
            "generate": "POST /generate",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=False
    )
