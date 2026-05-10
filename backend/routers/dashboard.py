from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("", response_model=schemas.DashboardStats)
def get_dashboard(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role == models.RoleEnum.ADMIN:
        tasks = db.query(models.Task).all()
        total_projects = db.query(models.Project).count()
    else:
        memberships = db.query(models.ProjectMember).filter(
            models.ProjectMember.user_id == current_user.id
        ).all()
        project_ids = [m.project_id for m in memberships]
        tasks = db.query(models.Task).filter(models.Task.project_id.in_(project_ids)).all()
        total_projects = len(project_ids)

    # Auto-mark overdue
    for task in tasks:
        if task.due_date and task.status not in (models.StatusEnum.DONE, models.StatusEnum.OVERDUE):
            if task.due_date < datetime.utcnow():
                task.status = models.StatusEnum.OVERDUE
    db.commit()

    todo = sum(1 for t in tasks if t.status == models.StatusEnum.TODO)
    in_progress = sum(1 for t in tasks if t.status == models.StatusEnum.IN_PROGRESS)
    done = sum(1 for t in tasks if t.status == models.StatusEnum.DONE)
    overdue = sum(1 for t in tasks if t.status == models.StatusEnum.OVERDUE)

    recent = sorted(tasks, key=lambda t: t.created_at, reverse=True)[:5]
    recent_out = []
    for t in recent:
        out = schemas.TaskOut.model_validate(t)
        out.assignee_name = t.assignee.name if t.assignee else None
        recent_out.append(out)

    return schemas.DashboardStats(
        total_tasks=len(tasks),
        todo=todo,
        in_progress=in_progress,
        done=done,
        overdue=overdue,
        total_projects=total_projects,
        recent_tasks=recent_out
    )
