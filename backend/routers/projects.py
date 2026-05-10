from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/projects", tags=["Projects"])

def check_project_access(project_id: str, user: models.User, db: Session):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if user.role == models.RoleEnum.ADMIN:
        return project
    membership = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == user.id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this project")
    return project

@router.get("", response_model=List[schemas.ProjectOut])
def list_projects(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role == models.RoleEnum.ADMIN:
        projects = db.query(models.Project).all()
    else:
        memberships = db.query(models.ProjectMember).filter(
            models.ProjectMember.user_id == current_user.id
        ).all()
        project_ids = [m.project_id for m in memberships]
        projects = db.query(models.Project).filter(models.Project.id.in_(project_ids)).all()

    result = []
    for p in projects:
        member_count = db.query(models.ProjectMember).filter(models.ProjectMember.project_id == p.id).count()
        task_count = db.query(models.Task).filter(models.Task.project_id == p.id).count()
        out = schemas.ProjectOut.model_validate(p)
        out.member_count = member_count
        out.task_count = task_count
        result.append(out)
    return result

@router.post("", response_model=schemas.ProjectOut, status_code=201)
def create_project(
    payload: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    project = models.Project(
        name=payload.name,
        description=payload.description,
        created_by=current_user.id
    )
    db.add(project)
    db.flush()

    # Auto-add creator as ADMIN member
    membership = models.ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role=models.RoleEnum.ADMIN
    )
    db.add(membership)
    db.commit()
    db.refresh(project)
    return project

@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    project = check_project_access(project_id, current_user, db)
    out = schemas.ProjectOut.model_validate(project)
    out.member_count = db.query(models.ProjectMember).filter(models.ProjectMember.project_id == project_id).count()
    out.task_count = db.query(models.Task).filter(models.Task.project_id == project_id).count()
    return out

@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_admin)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()

@router.post("/{project_id}/members", status_code=201)
def add_member(
    project_id: str,
    payload: schemas.AddMemberRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with that email not found")

    existing = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")

    member = models.ProjectMember(project_id=project_id, user_id=user.id, role=payload.role)
    db.add(member)
    db.commit()
    return {"message": f"{user.name} added to project"}

@router.get("/{project_id}/members", response_model=List[schemas.MemberOut])
def list_members(project_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    check_project_access(project_id, current_user, db)
    memberships = db.query(models.ProjectMember).filter(models.ProjectMember.project_id == project_id).all()
    result = []
    for m in memberships:
        result.append(schemas.MemberOut(
            id=m.id, user_id=m.user_id,
            name=m.user.name, email=m.user.email,
            role=m.role, joined_at=m.joined_at
        ))
    return result

@router.delete("/{project_id}/members/{user_id}", status_code=204)
def remove_member(
    project_id: str, user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin)
):
    membership = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == user_id
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(membership)
    db.commit()
