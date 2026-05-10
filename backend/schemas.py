from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from .models import RoleEnum, StatusEnum

# ── Auth ──────────────────────────────────────────────
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[RoleEnum] = RoleEnum.MEMBER

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: RoleEnum
    created_at: datetime
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

# ── Projects ──────────────────────────────────────────
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Project name cannot be empty")
        return v.strip()

class ProjectOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_by: str
    created_at: datetime
    member_count: Optional[int] = 0
    task_count: Optional[int] = 0
    model_config = {"from_attributes": True}

class AddMemberRequest(BaseModel):
    email: str
    role: Optional[RoleEnum] = RoleEnum.MEMBER

class MemberOut(BaseModel):
    id: str
    user_id: str
    name: str
    email: str
    role: RoleEnum
    joined_at: datetime
    model_config = {"from_attributes": True}

# ── Tasks ─────────────────────────────────────────────
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assignee_id: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[StatusEnum] = StatusEnum.TODO

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Task title cannot be empty")
        return v.strip()

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[StatusEnum] = None
    assignee_id: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: StatusEnum
    due_date: Optional[datetime]
    project_id: str
    assignee_id: Optional[str]
    assignee_name: Optional[str] = None
    created_by: str
    created_at: datetime
    model_config = {"from_attributes": True}

# ── Dashboard ─────────────────────────────────────────
class DashboardStats(BaseModel):
    total_tasks: int
    todo: int
    in_progress: int
    done: int
    overdue: int
    total_projects: int
    recent_tasks: List[TaskOut]
