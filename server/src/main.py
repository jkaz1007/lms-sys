
from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import List
from pymongo import MongoClient
from fastapi.responses import JSONResponse
from passlib.context import CryptContext

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["lms"]
users_collection = db["users"]

# FastAPI instance
app = FastAPI()

# Secret key to sign JWT tokens
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

# OAuth2PasswordBearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Create an instance of the CryptContext for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function to hash the password
def hash_password(password: str):
    return pwd_context.hash(password)


# Function to create JWT tokens
def create_jwt_token(data: dict):
    expires_delta = timedelta(minutes=120)
    expire = datetime.utcnow() + expires_delta
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Function to decode JWT tokens
def decode_jwt_token(token: str):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception


# Dependency to get current user from token
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_jwt_token(token)
    return payload


@app.post("/register")
async def register_user(request: Request):
    # Check if the user already exists in MongoDB
    payLoadJson = await request.json()
    empId = payLoadJson["employeeId"]
    password = payLoadJson["password"]
    role = payLoadJson["role"]
    if users_collection.find_one({"employeeId": empId}):
        raise HTTPException(
            status_code=400, detail="User with this employeeId already exists"
        )

    # Hash the password before storing it
    hashed_password = hash_password(password)

    # Store user details in MongoDB
    user_data = {"employeeId": empId, "password": hashed_password, "role": role}
    users_collection.insert_one(user_data)

    # Return a success message or user details if needed
    return JSONResponse(content={"message": "User registered successfully"})

@app.post("/login")
async def login(request: Request):
    payload_json = await request.json()
    employee_id = payload_json["employeeId"]
    password = payload_json["password"]

    # Check if the user exists in MongoDB
    user_data = users_collection.find_one({"employeeId": employee_id})

    if not user_data:
        raise HTTPException(
            status_code=401, detail="Invalid employeeId or password"
        )

    # Verify the password
    hashed_password = user_data["password"]
    if not pwd_context.verify(password, hashed_password):
        raise HTTPException(
            status_code=401, detail="Invalid employeeId or password"
        )

    # Generate a JWT token for the user
    token_data = {"sub": employee_id, "role": user_data["role"]}
    token = create_jwt_token(token_data)

    # Return the JWT token as part of the response
    return JSONResponse(content={"access_token": token, "token_type": "bearer"})


# FastAPI route to request leave
@app.post("/leave/request")
async def request_leave(request: Request, authorization: str = Header(...) ):
    print('----------leave request in progress------------------',authorization)
    token = authorization.split(" ")[1]
    current_user = get_current_user(token)
    # Implement logic to store leave request details in the database
    # Return a success message or leave request details if needed
    return current_user


# FastAPI route to approve/reject leave request (admin only)
@app.post("/leave/approve-reject")
async def approve_reject_leave(
    leave_request_id: str,
    approval_status: str,
    token: str = Depends(oauth2_scheme)
):
    current_user = get_current_user(token)
    # Implement logic to update leave request status in the database
    # Return a success message or updated leave request details if needed
    pass


# FastAPI route to get leave history for the current user
@app.get("/leave/history")
async def get_leave_history(token: str = Depends(oauth2_scheme)):
    current_user = get_current_user(token)
    # Implement logic to retrieve leave history from the database
    # Return a list of leave requests
    pass

# Function to start the FastAPI server
def start_server():
    import uvicorn

    # Use uvicorn to run the FastAPI application
    uvicorn.run(app, host="127.0.0.1", port=8000)


# Check if the script is run directly and start the server
if __name__ == "__main__":
    start_server()