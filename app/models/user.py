from pydantic import BaseModel

class User(BaseModel):
  _id: str
  username: str
  first_name: str
  middle_name: str
  email: str