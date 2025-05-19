def individual_serial(user) -> dict:
  return {
    "id": str(user["_id"]),
    "username": str(user["username"]),
    "first_name": user["first_name"],
    "middle_name": user["middle_name"],
    "last_name": user["last_name"]
  }

def list_serial(users) -> list:
  return [individual_serial(user) for user in users]