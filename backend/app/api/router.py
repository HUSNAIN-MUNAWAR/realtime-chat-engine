from fastapi import APIRouter
from app.api.routes import admin, auth, health, load_tests, mlops, messages, rooms, users, workspaces

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(mlops.router, prefix="/mlops", tags=["mlops"])
api_router.include_router(load_tests.router, prefix="/load-tests", tags=["load-tests"])
