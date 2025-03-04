from app import get_week_key
from replit import db

if __name__ == "__main__":
    key = get_week_key()

    if key not in db:
        print("KEY NOT FOUND")
    data = db[key]
    print(data)