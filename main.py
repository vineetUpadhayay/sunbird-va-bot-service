from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.routes import core


# Create a FastAPI app instance
app = FastAPI()

# Allow all origins with CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins, replace with specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers for notes and authentication
app.include_router(core.router, prefix="/api/core", tags=["core"])


# Redirect '/' to '/docs'
@app.get("/", include_in_schema=False)
def docs_redirect():
    return RedirectResponse("/docs")
