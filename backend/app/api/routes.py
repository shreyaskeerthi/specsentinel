"""API routes — auth, projects, team, async analysis, emails."""

import os
import shutil
import threading
import traceback
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db, SessionLocal
from app.models import User, Project, TeamMember, Milestone, Analysis
from app.auth import (
    hash_password, verify_password, create_access_token, get_current_user,
)
from app.services.analysis_pipeline import analysis_pipeline
from app.services.llm_extraction import llm_extraction_service

router = APIRouter()


# ──────────────────────────────────────────────
#  Schemas
# ──────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    company: str | None = None

class LoginRequest(BaseModel):
    email: str
    password: str

class ProjectCreate(BaseModel):
    name: str
    client_name: str | None = None
    description: str | None = None
    bid_due_date: str | None = None
    contract_value: float | None = None
    budget: float | None = None

class ProjectUpdate(BaseModel):
    name: str | None = None
    client_name: str | None = None
    description: str | None = None
    status: str | None = None
    bid_due_date: str | None = None
    contract_value: float | None = None
    budget: float | None = None
    contingency_percent: float | None = None

class TeamMemberCreate(BaseModel):
    name: str
    email: str | None = None
    role: str  # Estimator, PM, Finance, Ops, Superintendent, Executive
    phone: str | None = None

class TeamMemberUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    role: str | None = None
    phone: str | None = None

class MilestoneCreate(BaseModel):
    title: str
    date: str  # ISO date
    phase: str  # preconstruction, construction, closeout
    type: str = "milestone"  # milestone, deadline, task, blackout, meeting
    description: str | None = None
    assignee: str | None = None

class MilestoneUpdate(BaseModel):
    title: str | None = None
    date: str | None = None
    phase: str | None = None
    type: str | None = None
    description: str | None = None
    status: str | None = None
    assignee: str | None = None

class MeetingNotesRequest(BaseModel):
    notes: str
    project_id: str | None = None

class EmailGenerateRequest(BaseModel):
    analysis_id: str

class InviteRequest(BaseModel):
    member_id: str


# ──────────────────────────────────────────────
#  Auth
# ──────────────────────────────────────────────

@router.post("/auth/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(400, "Email already registered")
    user = User(
        email=req.email,
        full_name=req.full_name,
        company=req.company,
        hashed_password=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    return {
        "token": token,
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "company": user.company},
    }


@router.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")
    token = create_access_token(user.id)
    return {
        "token": token,
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "company": user.company},
    }


@router.get("/auth/me")
def get_me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "company": user.company}


# ──────────────────────────────────────────────
#  Projects
# ──────────────────────────────────────────────

@router.get("/projects")
def list_projects(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    projects = db.query(Project).filter(Project.owner_id == user.id).order_by(Project.created_at.desc()).all()
    results = []
    for p in projects:
        doc_count = db.query(Analysis).filter(
            Analysis.project_id == p.id, Analysis.source_type == "document"
        ).count()
        team_count = db.query(TeamMember).filter(TeamMember.project_id == p.id).count()
        results.append({
            "id": p.id,
            "name": p.name,
            "client_name": p.client_name,
            "status": p.status,
            "bid_due_date": p.bid_due_date,
            "contract_value": p.contract_value,
            "budget": p.budget,
            "contingency_percent": p.contingency_percent,
            "document_count": doc_count,
            "team_count": team_count,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })
    return results


@router.post("/projects")
def create_project(
    req: ProjectCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = Project(
        name=req.name,
        client_name=req.client_name,
        description=req.description,
        bid_due_date=req.bid_due_date,
        contract_value=req.contract_value,
        budget=req.budget,
        owner_id=user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return _project_detail(project, db)


@router.get("/projects/{project_id}")
def get_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    return _project_detail(project, db)


@router.patch("/projects/{project_id}")
def update_project(
    project_id: str,
    req: ProjectUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return _project_detail(project, db)


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    db.delete(project)
    db.commit()
    return {"status": "deleted"}


def _project_detail(project: Project, db: Session) -> dict:
    analyses = db.query(Analysis).filter(Analysis.project_id == project.id).order_by(Analysis.created_at.desc()).all()
    team = db.query(TeamMember).filter(TeamMember.project_id == project.id).all()
    milestones = db.query(Milestone).filter(Milestone.project_id == project.id).order_by(Milestone.date).all()

    milestones_by_phase = {"preconstruction": [], "construction": [], "closeout": []}
    for m in milestones:
        phase = m.phase if m.phase in milestones_by_phase else "construction"
        milestones_by_phase[phase].append({
            "id": m.id, "title": m.title, "date": m.date, "phase": m.phase,
            "type": m.type, "description": m.description, "status": m.status,
            "assignee": m.assignee,
        })

    return {
        "id": project.id,
        "name": project.name,
        "client_name": project.client_name,
        "description": project.description,
        "status": project.status,
        "bid_due_date": project.bid_due_date,
        "contract_value": project.contract_value,
        "budget": project.budget,
        "contingency_percent": project.contingency_percent,
        "owner_id": project.owner_id,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        "team_members": [
            {
                "id": m.id, "name": m.name, "email": m.email,
                "role": m.role, "phone": m.phone, "invited": m.invited,
            }
            for m in team
        ],
        "analyses": [
            {
                "id": a.id, "filename": a.filename, "source_type": a.source_type,
                "status": a.status, "page_count": a.page_count,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "has_risk_report": a.risk_report is not None,
                "overall_risk_level": (a.risk_report or {}).get("overall_risk_level"),
                "recommendation": ((a.risk_report or {}).get("go_no_go") or {}).get("recommendation"),
            }
            for a in analyses
        ],
        "milestones": milestones_by_phase,
    }


# ──────────────────────────────────────────────
#  Team Members
# ──────────────────────────────────────────────

@router.post("/projects/{project_id}/team")
def add_team_member(
    project_id: str,
    req: TeamMemberCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    member = TeamMember(
        project_id=project_id,
        name=req.name,
        email=req.email,
        role=req.role,
        phone=req.phone,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return {"id": member.id, "name": member.name, "email": member.email, "role": member.role, "phone": member.phone, "invited": member.invited}


@router.patch("/projects/{project_id}/team/{member_id}")
def update_team_member(
    project_id: str,
    member_id: str,
    req: TeamMemberUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    member = db.query(TeamMember).filter(TeamMember.id == member_id, TeamMember.project_id == project_id).first()
    if not member:
        raise HTTPException(404, "Team member not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    db.commit()
    db.refresh(member)
    return {"id": member.id, "name": member.name, "email": member.email, "role": member.role, "phone": member.phone, "invited": member.invited}


@router.delete("/projects/{project_id}/team/{member_id}")
def remove_team_member(
    project_id: str,
    member_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    member = db.query(TeamMember).filter(TeamMember.id == member_id, TeamMember.project_id == project_id).first()
    if not member:
        raise HTTPException(404, "Team member not found")
    db.delete(member)
    db.commit()
    return {"status": "removed"}


@router.post("/projects/{project_id}/team/{member_id}/invite")
def invite_team_member(
    project_id: str,
    member_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    member = db.query(TeamMember).filter(TeamMember.id == member_id, TeamMember.project_id == project_id).first()
    if not member:
        raise HTTPException(404, "Team member not found")
    if not member.email:
        raise HTTPException(400, "Member has no email address")
    member.invited = "pending"
    db.commit()
    # In production: send actual email here
    return {"status": "invited", "message": f"Invitation sent to {member.email}"}


# ──────────────────────────────────────────────
#  Milestones (Preconstruction / Construction / Closeout)
# ──────────────────────────────────────────────

@router.post("/projects/{project_id}/milestones")
def create_milestone(
    project_id: str,
    req: MilestoneCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    m = Milestone(
        project_id=project_id,
        title=req.title,
        date=req.date,
        phase=req.phase,
        type=req.type,
        description=req.description,
        assignee=req.assignee,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return {"id": m.id, "title": m.title, "date": m.date, "phase": m.phase, "type": m.type, "description": m.description, "status": m.status, "assignee": m.assignee}


@router.patch("/projects/{project_id}/milestones/{milestone_id}")
def update_milestone(
    project_id: str,
    milestone_id: str,
    req: MilestoneUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    m = db.query(Milestone).filter(Milestone.id == milestone_id, Milestone.project_id == project_id).first()
    if not m:
        raise HTTPException(404, "Milestone not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(m, field, value)
    db.commit()
    db.refresh(m)
    return {"id": m.id, "title": m.title, "date": m.date, "phase": m.phase, "type": m.type, "description": m.description, "status": m.status, "assignee": m.assignee}


@router.delete("/projects/{project_id}/milestones/{milestone_id}")
def delete_milestone(
    project_id: str,
    milestone_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    m = db.query(Milestone).filter(Milestone.id == milestone_id, Milestone.project_id == project_id).first()
    if not m:
        raise HTTPException(404, "Milestone not found")
    db.delete(m)
    db.commit()
    return {"status": "deleted"}


# ──────────────────────────────────────────────
#  Upload & Analysis (ASYNC — no timeout)
# ──────────────────────────────────────────────

def _run_analysis_background(analysis_id: str, file_path: str, filename: str):
    """Run analysis in background thread."""
    db = SessionLocal()
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            return
        analysis.status = "processing"
        db.commit()

        result = analysis_pipeline.process_document(file_path, filename)

        analysis.page_count = result.get("page_count")
        analysis.extraction_data = result.get("extraction")
        analysis.risk_report = result.get("risk_report")
        analysis.division_data = result.get("division_data")
        analysis.action_board = result.get("action_board")
        analysis.chunks_data = result.get("chunks")
        analysis.status = "completed"
        db.commit()
    except Exception as e:
        traceback.print_exc()
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            analysis.status = "failed"
            analysis.error_message = str(e)
            db.commit()
    finally:
        # Cleanup file
        try:
            os.unlink(file_path)
        except OSError:
            pass
        db.close()


@router.post("/projects/{project_id}/upload")
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a PDF — starts analysis in background, returns immediately."""
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted")

    # Save file
    file_id = str(uuid.uuid4())
    upload_dir = Path(settings.FILE_STORAGE_PATH)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{file_id}.pdf"

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Create analysis record
    analysis = Analysis(
        project_id=project_id,
        filename=file.filename,
        source_type="document",
        status="pending",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # Start background analysis — NO TIMEOUT
    thread = threading.Thread(
        target=_run_analysis_background,
        args=(analysis.id, str(file_path), file.filename),
        daemon=True,
    )
    thread.start()

    return {"analysis_id": analysis.id, "status": "pending", "filename": file.filename}


@router.get("/analysis/{analysis_id}")
def get_analysis(
    analysis_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get analysis — poll this until status is 'completed'."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(404, "Analysis not found")
    # Verify ownership via project
    project = db.query(Project).filter(Project.id == analysis.project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Analysis not found")

    result = {
        "id": analysis.id,
        "project_id": analysis.project_id,
        "filename": analysis.filename,
        "source_type": analysis.source_type,
        "status": analysis.status,
        "error_message": analysis.error_message,
        "page_count": analysis.page_count,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
    }

    if analysis.status == "completed":
        result.update({
            "extraction": analysis.extraction_data,
            "risk_report": analysis.risk_report,
            "division_data": analysis.division_data,
            "action_board": analysis.action_board,
            "meeting_result": analysis.meeting_result,
            "email_set": analysis.email_set,
        })

    return result


# ──────────────────────────────────────────────
#  Meeting Notes (also async)
# ──────────────────────────────────────────────

def _run_meeting_analysis_background(analysis_id: str, notes: str, existing_data: dict | None, doc_analysis_id: str | None = None):
    """Run meeting notes analysis and MERGE into existing doc analysis."""
    db = SessionLocal()
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            return
        analysis.status = "processing"
        db.commit()

        result = llm_extraction_service.analyze_meeting_notes(notes, existing_data)
        meeting_data = result.model_dump()
        analysis.meeting_result = meeting_data
        analysis.status = "completed"
        db.commit()

        # MERGE into existing document analysis if one exists
        if doc_analysis_id:
            doc_analysis = db.query(Analysis).filter(Analysis.id == doc_analysis_id).first()
            if doc_analysis and doc_analysis.risk_report:
                rr = dict(doc_analysis.risk_report)

                # Merge new risks into flags
                for nr in meeting_data.get("new_risks", []):
                    rr.setdefault("flags", []).append({
                        "id": f"MR{len(rr.get('flags', []))+1}",
                        "type": "scope",
                        "severity": nr.get("severity", "medium"),
                        "title": nr.get("title", ""),
                        "description": nr.get("description", ""),
                        "source_quote": "From meeting notes",
                        "responsibility": nr.get("responsibility", "shared"),
                        "category": "Meeting Update",
                        "cost_impact": {
                            "type": "fixed" if nr.get("cost_impact_min") else "none",
                            "min_dollars": nr.get("cost_impact_min"),
                            "max_dollars": nr.get("cost_impact_max"),
                            "description": nr.get("cost_impact_description"),
                        },
                        "impact": [nr.get("description", "")],
                        "recommended_action": [],
                    })
                rr["total_flags"] = len(rr.get("flags", []))
                rr["high_severity_count"] = sum(
                    1 for f in rr.get("flags", [])
                    if f.get("severity") in ("high", "critical")
                )

                # Update financial exposure
                if meeting_data.get("revised_exposure_min") or meeting_data.get("revised_exposure_max"):
                    fe = rr.get("financial_exposure") or {}
                    if meeting_data.get("revised_exposure_min"):
                        fe["total_identified_min"] = meeting_data["revised_exposure_min"]
                    if meeting_data.get("revised_exposure_max"):
                        fe["total_identified_max"] = meeting_data["revised_exposure_max"]
                    rr["financial_exposure"] = fe

                doc_analysis.risk_report = rr

                # Merge tasks into action board
                ab = dict(doc_analysis.action_board or {})
                for task in meeting_data.get("updated_tasks", []):
                    cat = task.get("category", "internal")
                    col = ab.setdefault(cat, [])
                    col.append({
                        "id": f"MT{len(col)+1}",
                        "title": task.get("title", ""),
                        "description": task.get("description", ""),
                        "priority": task.get("priority", "medium"),
                        "owner_type": task.get("owner_type", "PM"),
                        "category": cat,
                        "linked_risk_id": None,
                        "page_reference": None,
                        "due_date": task.get("due_date"),
                        "assignee": task.get("assignee"),
                        "status": "open",
                    })
                doc_analysis.action_board = ab

                db.commit()

    except Exception as e:
        traceback.print_exc()
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            analysis.status = "failed"
            analysis.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/projects/{project_id}/meeting-notes")
def analyze_meeting_notes(
    project_id: str,
    req: MeetingNotesRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    # Find existing analysis for context
    existing = db.query(Analysis).filter(
        Analysis.project_id == project_id,
        Analysis.source_type == "document",
        Analysis.status == "completed",
    ).order_by(Analysis.created_at.desc()).first()

    existing_data = None
    if existing and existing.risk_report:
        existing_data = {"risk_report": existing.risk_report}

    analysis = Analysis(
        project_id=project_id,
        source_type="meeting_notes",
        status="pending",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    doc_analysis_id = existing.id if existing else None

    thread = threading.Thread(
        target=_run_meeting_analysis_background,
        args=(analysis.id, req.notes, existing_data, doc_analysis_id),
        daemon=True,
    )
    thread.start()

    return {"analysis_id": analysis.id, "status": "pending", "merging_into": doc_analysis_id}


# ──────────────────────────────────────────────
#  Email Generation
# ──────────────────────────────────────────────

@router.post("/analysis/{analysis_id}/generate-emails")
def generate_emails(
    analysis_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(404, "Analysis not found")
    project = db.query(Project).filter(Project.id == analysis.project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Not found")

    if not analysis.risk_report:
        raise HTTPException(400, "Analysis not complete yet")

    # Get team members for email recipients
    team = db.query(TeamMember).filter(TeamMember.project_id == project.id).all()
    team_context = {m.role: {"name": m.name, "email": m.email} for m in team}

    analysis_data = {
        "risk_report": analysis.risk_report,
        "team_members": team_context,
        "project_name": project.name,
        "contract_value": project.contract_value,
    }

    result = llm_extraction_service.generate_emails(analysis_data)
    analysis.email_set = result.model_dump()
    db.commit()

    return result.model_dump()


@router.post("/send-email")
def send_email(body: dict, user: User = Depends(get_current_user)):
    """Simulate sending an email."""
    return {"status": "sent", "message": f"Email sent to {body.get('recipients', 'recipients')}"}
