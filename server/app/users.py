from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from .auth import hash_password, create_jwt_token, decode_jwt_token, oauth2_scheme, pwd_context, get_current_user
from .database import users_collection, leave_types_collection
from .models import User, LeaveCredit
from .utils import parse_json

router = APIRouter()

@router.post("/register")
async def register_user(request: Request, user: User):
    # Check if the user already exists in MongoDB
    print('user',user)
    payLoadJson = await request.json()
    empId = user.employeeId
    password = user.password
    empName = user.empName
    empEmail = user.empEmail
    empPhone = user.empPhone
    empManagerId = user.empManagerId
    role = user.role
    if users_collection.find_one({"employeeId": empId}):
        raise HTTPException(
            status_code=400, detail="User with this employeeId already exists"
        )

    # Hash the password before storing it
    hashed_password = hash_password(password)

    # Store user details in MongoDB
    user_data = {"employeeId": empId, "password": hashed_password,
                 "role": role, "empName": empName, "empEmail": empEmail, "empPhone": empPhone, "empManagerId": empManagerId}
    # Fetch leave types that are available for employees
    available_leave_types = list(leave_types_collection.find({"available_for_employees": True}))

        # Credit only available leave types to the user
    user_data["leave_credits"] = []
    for leave_type in available_leave_types:
        leave_credit_data = {
            "leaveType": leave_type["name"],
            "quota": leave_type["quota"],
            "used": 0,
            "available": leave_type["quota"]
        }
        user_data["leave_credits"].append(leave_credit_data)
    users_collection.insert_one(user_data)

    # Return a success message or user details if needed
    return JSONResponse(content={"message": "User registered successfully"})

@router.post("/login")
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
    
    #todo: current architecture doesnt propagates leaveType changes/additions to old users
    # so for that to happen think os some architectural chnages to detect leaveType updates/additions
    # while the user tries to log in and if change is detected update user's leave_credits

    # Generate a JWT token for the user
    user_details = {
        "employeeId": user_data["employeeId"],
        "role": user_data["role"],
        "empName": user_data["empName"],
        "empEmail": user_data["empEmail"],
        "empPhone": user_data["empPhone"],
        "empManagerId": user_data["empManagerId"],
        "leave_credits": user_data.get("leave_credits", [])
    }
    token = create_jwt_token(user_details)

    # Return the JWT token as part of the response
    return JSONResponse(content={"access_token": token, "token_type": "bearer", "data": parse_json(user_data)})

@router.post("/verify-loggedin-user")
async def login(request: Request,authorization: str = Header(...)):
    token = authorization.split(" ")[1]
    current_user = get_current_user(token)

    # Return the JWT token as part of the response
    return JSONResponse(content={"data": parse_json(current_user), "message": "user verified"})