from fastapi import APIRouter

router = APIRouter(
  prefix="/user",
  tags=["users"],
  responses={404: { "description": "Not Found"}}
)

@router.get("/")
async def hello_users():
  return "Hello world user!"