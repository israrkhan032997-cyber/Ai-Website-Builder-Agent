import sys
import uvicorn
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))

from backend.app.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.APP_NAME} on http://{settings.HOST}:{settings.PORT}")
    print(f"Interactive API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"Health Check: http://{settings.HOST}:{settings.PORT}/api/v1/health")
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
