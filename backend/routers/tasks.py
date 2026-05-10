from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api", tags=["Tasks"])

def get_member_role(project_id: str, user_id: str, db: Session):
    if True:  # Check global admin first
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user and user.role == models.RoleEnum.ADMIN:
            return models.RoleEnum.ADMIN
    m = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == user_id
    ).first()
    return m.role if m else None

def auto_update_overdue(task: models.Task):
    if task.due_date and task.status not in (models.StatusEnum.DONE,):
        if task.due_date < datetime.utcnow():
            task.status = models.StatusEnum.OVERDUE

@router.get("/projects/{project_id}/tasks", response_model=List[schemas.TaskOut])
def list_tasks(project_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    role = get_member_role(project_id, current_user.id, db)
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this project")

    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()
    result = []
    for t in tasks:
        auto_update_overdue(t)
        out = schemas.TaskOut.model_validate(t)
        out.assignee_name = t.assignee.name if t.assignee else None
        result.append(out)
    db.commit()
    return result

@router.post("/projects/{project_id}/tasks", response_model=schemas.TaskOut, status_code=201)
def create_task(
    project_id: str,
    payload: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    role = get_member_role(project_id, current_user.id, db)
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this project")

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate assignee is a member
    if payload.assignee_id:
        assignee_role = get_member_role(project_id, payload.assignee_id, db)
        if not assignee_role:
            raise HTTPException(status_code=400, detail="Assignee is not a project member")

    task = models.Task(
        title=payload.title,
        description=payload.description,
        status=payload.status,
        due_date=payload.due_date,
        project_id=project_id,
        assignee_id=payload.assignee_id,
        created_by=current_user.id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    out = schemas.TaskOut.model_validate(task)
    out.assignee_name = task.assignee.name if task.assignee else None
    return out

@router.patch("/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(
    task_id: str,
    payload: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    role = get_member_role(task.project_id, current_user.id, db)
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this project")

    # Members can only update status of tasks assigned to them
    if role == models.RoleEnum.MEMBER:
        if task.assignee_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only update tasks assigned to you")
        if payload.title or payload.assignee_id or payload.due_date:
            raise HTTPException(status_code=403, detail="Members can only update status")

    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.status is not None:
        task.status = payload.status
    if payload.assignee_id is not None:
        task.assignee_id = payload.assignee_id
    if payload.due_date is not None:
        task.due_date = payload.due_date

    db.commit()
    db.refresh(task)
    out = schemas.TaskOut.model_validate(task)
    out.assignee_name = task.assignee.name if task.assignee else None
    return out

@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_admin)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
