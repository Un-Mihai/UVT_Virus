from fastapi import APIRouter

from app.auth import CurrentUser, User

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/me")
async def me(user: CurrentUser) -> User:
    """The signed-in user, as the API sees them after checking the token."""
    return user
