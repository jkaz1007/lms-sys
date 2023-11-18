from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from .models import LeaveType
from .database import leave_types_collection
from .utils import parse_json

router = APIRouter()

# Create LeaveType
@router.post("/leave-types/create", response_model=LeaveType)
async def create_leave_type(leave_type: LeaveType):
    try:
        existing_leave_type = leave_types_collection.find_one({"name": leave_type.name})
        if existing_leave_type:
            raise HTTPException(status_code=400, detail="Leave type with this name already exists")

        leave_type_dict = leave_type.model_dump()
        result = leave_types_collection.insert_one(leave_type_dict)
        print('insertedResult',result)
        return JSONResponse(content={"message": "Leave type created successfully", "data": parse_json(leave_type_dict)})
    except Exception as e:
        return JSONResponse(content={"message": "Error creating leave type", "error": str(e)}, status_code=500)

# Get All LeaveTypes
@router.get("/leave-types", response_model=list[LeaveType])
async def get_all_leave_types():
    try:
        leave_types = list(leave_types_collection.find())
        return JSONResponse(content={"message": "Leave types retrieved successfully", "data": parse_json(leave_types)})
    except Exception as e:
        return JSONResponse(content={"message": "Error retrieving leave types", "error": str(e)}, status_code=500)

# Get LeaveType by Name
@router.get("/leave-types/{leave_type_name}", response_model=LeaveType)
async def get_leave_type(leave_type_name: str):
    try:
        leave_type = leave_types_collection.find_one({"name": leave_type_name})
        if not leave_type:
            raise HTTPException(status_code=404, detail="Leave type not found")
        return JSONResponse(content={"message": "Leave type retrieved successfully", "data": leave_type})
    except Exception as e:
        return JSONResponse(content={"message": "Error retrieving leave type", "error": str(e)}, status_code=500)

# Update LeaveType
@router.put("/leave-types/{leave_type_name}", response_model=LeaveType)
async def update_leave_type(leave_type_name: str, leave_type: LeaveType):
    try:
        existing_leave_type = leave_types_collection.find_one({"name": leave_type_name})
        if not existing_leave_type:
            raise HTTPException(status_code=404, detail="Leave type not found")

        leave_types_collection.update_one({"name": leave_type_name}, {"$set": leave_type.dict()})
        return JSONResponse(content={"message": "Leave type updated successfully", "data": leave_type})
    except Exception as e:
        return JSONResponse(content={"message": "Error updating leave type", "error": str(e)}, status_code=500)

# Delete LeaveType
@router.delete("/leave-types/{leave_type_name}", response_model=LeaveType)
async def delete_leave_type(leave_type_name: str):
    try:
        leave_type = leave_types_collection.find_one({"name": leave_type_name})
        if not leave_type:
            raise HTTPException(status_code=404, detail="Leave type not found")

        leave_types_collection.delete_one({"name": leave_type_name})
        return JSONResponse(content={"message": "Leave type deleted successfully", "data": leave_type})
    except Exception as e:
        return JSONResponse(content={"message": "Error deleting leave type", "error": str(e)}, status_code=500)
