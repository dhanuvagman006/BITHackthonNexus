import uvicorn
import os

if __name__ == "__main__":
    # Pointing back to the full PhoenixVault application
    # uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)

     # Pointing to the new simplified demo server
    uvicorn.run("backend.index:app", host="0.0.0.0", port=8008, reload=False)
