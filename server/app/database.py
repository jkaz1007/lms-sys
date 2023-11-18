from pymongo import MongoClient

#mongo connection
client = MongoClient("mongodb://localhost:27017/")
db = client["lms"]
users_collection = db["users"]
leave_types_collection = db["leave_types_collection"]
leaves_collection = db["leaves"]