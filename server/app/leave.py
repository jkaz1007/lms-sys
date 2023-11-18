from fastapi import APIRouter, Depends, HTTPException, Request, Header, Query, Path, Body
from fastapi.responses import JSONResponse
from .auth import oauth2_scheme, get_current_user
from .models import User, Leave
from .database import users_collection, leaves_collection
from datetime import datetime
from .utils import parse_json
from bson.objectid import ObjectId
import json

router = APIRouter()

@router.post("/leave/request")
async def request_leave(request: Request, leave: Leave, authorization: str = Header(...)):
    try:
        # Retrieve the current user from the token
        token = authorization.split(" ")[1]
        current_user = get_current_user(token)
        
        # Retrieve the user's leave credits from the users collection
        user_leave_credits = next((credit for credit in current_user["leave_credits"] if credit["leaveType"] == leave.leaveType), None)

        # Check if the user has enough leave balance for the requested leave type
        if not user_leave_credits:
            raise HTTPException(status_code=400, detail="Invalid leave request or insufficient leave balance")

        # Parse the date strings and convert them to datetime objects
        leave_start_date = datetime.strptime(leave.startDate, '%d/%m/%Y')
        leave_end_date = datetime.strptime(leave.endDate, '%d/%m/%Y')

        # Calculate the number of days for the leave request
        num_days = (leave_end_date - leave_start_date).days + 1
        print('numDays',num_days)

        # Check if the user has enough available leave balance
        if user_leave_credits["available"] < num_days:
            raise HTTPException(status_code=400, detail="Insufficient leave balance")

        # Register the leave by adding a document to the leaves collection
        leave_data = {
            "employeeId": current_user["employeeId"],
            "managerId": current_user["empManagerId"],
            "leaveType": leave.leaveType,
            "startDate": leave_start_date,
            "endDate": leave_end_date,
            "status": 'ACTION_PENDING',
            "comments": leave.comments,
            "empName": current_user["empName"]
        }

        leaves_collection.insert_one(leave_data)

        #todo: move leave balance update logic to leave request approve/reject API
        # Update the user's leave balance in the users collection
        # new_used_balance = user_leave_credits["used"] + num_days
        # new_available_balance = user_leave_credits["available"] - num_days

        # users_collection.update_one(
        #     {"employeeId": leave.employeeId, "leave_credits.leaveType": leave.leaveType},
        #     {
        #         "$set": {
        #             "leave_credits.$.used": new_used_balance,
        #             "leave_credits.$.available": new_available_balance
        #         }
        #     }
        # )

        # Return a success message or leave details if needed
        return JSONResponse(content={"message": "Leave request registered successfully","data": parse_json(leave_data)})
    except HTTPException as e:
        # Handle FastAPI HTTPExceptions
        return JSONResponse(content={"message": "Error in leave request", "error": str(e)}, status_code=e.status_code)
    except Exception as e:
        # Handle other exceptions
        return JSONResponse(content={"message": "Internal server error", "error": str(e)}, status_code=500)

@router.patch("/leave/update-status/{leave_request_id}")
async def update_leave_status(
    request: Request,
    leave_request_id: str = Path(..., title="Leave Request ID", description="The ID of the leave request to update."),
    authorization: str = Header(...),
):
    try:
        requestPayloadJson = await request.json()
        approval_status = requestPayloadJson["approval_status"]
        # Extract token from the authorization header
        token = authorization.split(" ")[1]

        # Get the current user details from the token
        current_user = get_current_user(token)

        # Check if the current user has the necessary role to approve/reject
        allowed_roles = ["admin", "approver", "reviewer"]
        if approval_status in ['approved', 'rejected'] and current_user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="User does not have permission to update leave status")

        # Get the leave document using leave_request_id
        leave_data = leaves_collection.find_one({"_id": ObjectId(leave_request_id)})
        if not leave_data:
            raise HTTPException(status_code=404, detail="Leave request not found")
        # Check if the current user is authorized approve or reject
        if approval_status in ['approved', 'rejected'] and current_user["employeeId"] != leave_data["managerId"]:
            raise HTTPException(status_code=401, detail="Unauthorized to update leave status")

        # If the status is approved, update the user's leave balance
        if approval_status.lower() == "approved":
            leave_applier_user_details = users_collection.find_one({"employeeId": leave_data["employeeId"]})
            user_leave_details = leave_applier_user_details["leave_credits"]
            applied_leave_type = leave_data["leaveType"]
            matching_leave_details = next((leave for leave in user_leave_details if leave["leaveType"] == applied_leave_type), None)
            # Calculate the number of days for the leave request
            num_days = (leave_data["endDate"] - leave_data["startDate"]).days + 1
            new_used_balance = matching_leave_details["used"] + num_days
            new_available_balance = matching_leave_details["available"] - num_days

            users_collection.update_one(
                {"employeeId": leave_data["employeeId"], "leave_credits.leaveType": leave_data["leaveType"]},
                {
                    "$set": {
                        "leave_credits.$.used": new_used_balance,
                        "leave_credits.$.available": new_available_balance
                    }
                }
            )
        # Update the leave status
        leaves_collection.update_one(
            {"_id": ObjectId(leave_request_id)},
            {"$set": {"status": approval_status}}
        )


        return JSONResponse(content={"message": "Leave status updated successfully"})

    except HTTPException as e:
        # Catch FastAPI-specific HTTP exceptions and return the appropriate response
        return JSONResponse(content={"message": str(e)}, status_code=e.status_code)

    except Exception as e:
        # Handle unexpected exceptions
        return JSONResponse(
            content={"message": "Internal Server Error", "error": str(e)},
            status_code=500,
        )

@router.get("/leave/myLeaves")
async def get_user_leaves(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    authorization: str = Header(...),
):
    try:
        # Extract token from the authorization header
        token = authorization.split(" ")[1]

        # Get the current user details from the token
        current_user = get_current_user(token)

        # Retrieve leaves for the current user using employeeId
        leave_records = list(leaves_collection.find({"employeeId": current_user["employeeId"]}).skip((page - 1) * page_size).limit(page_size))

        # Apply pagination to the result
        total_leaves = len(leave_records)

        return JSONResponse(
            content={
                "total_leaves": total_leaves,
                "page": page,
                "page_size": page_size,
                "leaves": parse_json(leave_records),
            }
        )
    except Exception as e:
        # Handle unexpected exceptions
        return JSONResponse(
            content={"message": "Error retrieving user leaves", "error": str(e)},
            status_code=500,
        )

@router.get("/leave/leaves-to-review")
async def get_leaves_to_review(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    authorization: str = Header(...),
):
    try:
        # Extract token from the authorization header
        token = authorization.split(" ")[1]

        # Get the current user details from the token
        current_user = get_current_user(token)

        # Retrieve leaves to review for the current user using managerId
        leave_records = list(leaves_collection.find({"managerId": current_user["employeeId"]}).skip((page - 1) * page_size).limit(page_size))

        # Apply pagination to the result
        total_leaves = len(leave_records)

        # Return the paginated result as JSON
        return JSONResponse(
            content={
                "total_leaves": total_leaves,
                "page": page,
                "page_size": page_size,
                "leaves_to_review": parse_json(leave_records),
            }
        )
    except Exception as e:
        # Handle unexpected exceptions
        return JSONResponse(
            content={"message": "Error retrieving leaves to review", "error": str(e)},
            status_code=500,
        )