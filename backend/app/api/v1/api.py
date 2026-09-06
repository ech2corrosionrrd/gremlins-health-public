from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, gremlins, activities, marketplace, quests

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(gremlins.router, prefix="/gremlins", tags=["Gremlins (Tamagotchi)"])
api_router.include_router(activities.router, prefix="/activities", tags=["Activities & Anti-Cheat"])
api_router.include_router(marketplace.router, prefix="/marketplace", tags=["Marketplace & cNFT"])
api_router.include_router(quests.router, prefix="/quests", tags=["Quests & Raid Bosses"])
