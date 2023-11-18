from pydantic import BaseModel, constr
from datetime import datetime
from typing import List, Optional


class LeaveCredit(BaseModel):
    leaveType: str
    quota: int
    used: int = 0
    available: int

class User(BaseModel):
    employeeId: str
    password: str
    role: str
    empName: str
    empEmail: str
    empPhone: str
    empManagerId: str
    leave_credits: List[LeaveCredit] = []

class Leave(BaseModel):
    # employeeId: Optional[str]
    # managerId: Optional[str]
    leaveType: str
    startDate: str  # DD/MM/YYYY format
    endDate: str  # DD/MM/YYYY format
    status: str = "ACTION_PENDING"
    comments: str = ""

class LeaveType(BaseModel):
    name: str
    quota: int
    available_for_employees: bool