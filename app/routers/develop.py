from fastapi import APIRouter, Query, HTTPException, Path

router = APIRouter(
  prefix="/develop",
  tags=["develop"],
  responses={404: { "description": "Not Found"}}
)

@router.get("/service1")
async def service_1():
  return "OK"