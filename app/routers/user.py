from fastapi import APIRouter

router = APIRouter(
  prefix="/user",
  tags=["users"],
  responses={404: { "description": "Not Found"}}
)

@router.get("/")
async def get_users():
  return "Get users api is under construction!"