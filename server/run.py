from app.main import app

if __name__ == "__main__":
    import uvicorn
    # uvicorn.run(app, host="127.0.0.1", port=8000, reload=True) #todo: use this in prod
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)