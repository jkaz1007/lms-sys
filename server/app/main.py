from fastapi import FastAPI
from .auth import oauth2_scheme
from .leave import router as leave_router
from .users import router as users_router
from .leaveTypes import router as leave_types_router

app = FastAPI()

app.include_router(leave_types_router, prefix="/api")
app.include_router(leave_router, prefix="/api")
app.include_router(users_router, prefix="/api")