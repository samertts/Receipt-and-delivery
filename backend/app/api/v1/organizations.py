from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.audit import log_audit
from app.core.exceptions import ConflictError, NotFoundError
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.transaction import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)

router = APIRouter(prefix="/organizations", tags=["المؤسسات"])


@router.get("", response_model=list[OrganizationResponse])
def list_organizations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    _active_only: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("view_organizations")),
):
    query = db.query(Organization)
    total_count = query.count()
    items = query.order_by(Organization.name).offset((page - 1) * limit).limit(limit).all()
    return JSONResponse(
        content=[OrganizationResponse.model_validate(o).model_dump(mode="json") for o in items],
        headers={"X-Total-Count": str(total_count)},
    )


@router.post("", response_model=OrganizationResponse, status_code=201)
def create_organization(
    payload: OrganizationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_organizations")),
):
    existing = db.query(Organization).filter(Organization.code == payload.code).first()
    if existing:
        raise ConflictError(f"رمز المؤسسة {payload.code} موجود مسبقاً")

    org = Organization(
        name=payload.name,
        code=payload.code,
        address=payload.address or "",
        phone=payload.phone or "",
        email=payload.email or "",
        logo_path=payload.logo_path or "",
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    log_audit(
        user_id=str(current_user.id),
        action_type="org_created",
        request=request,
        details=f"إنشاء مؤسسة: {org.name} ({org.code})",
        db=db,
    )
    return org


@router.get("/{org_id}", response_model=OrganizationResponse)
def get_organization(
    org_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("view_organizations")),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise NotFoundError("المؤسسة غير موجودة")
    return org


@router.put("/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: str,
    payload: OrganizationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_organizations")),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise NotFoundError("المؤسسة غير موجودة")

    if payload.name is not None:
        org.name = payload.name
    if payload.code is not None:
        existing = db.query(Organization).filter(
            Organization.code == payload.code, Organization.id != org_id,
        ).first()
        if existing:
            raise ConflictError(f"رمز المؤسسة {payload.code} موجود مسبقاً")
        org.code = payload.code
    if payload.address is not None:
        org.address = payload.address
    if payload.phone is not None:
        org.phone = payload.phone
    if payload.email is not None:
        org.email = payload.email

    db.commit()
    db.refresh(org)

    log_audit(
        user_id=str(current_user.id),
        action_type="org_updated",
        request=request,
        details=f"تحديث مؤسسة: {org.name}",
        db=db,
    )
    return org


@router.delete("/{org_id}", status_code=204)
def delete_organization(
    org_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_organizations")),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise NotFoundError("المؤسسة غير موجودة")
    db.delete(org)
    db.commit()

    log_audit(
        user_id=str(current_user.id),
        action_type="org_deleted",
        request=request,
        details=f"حذف مؤسسة: {org.name} ({org.code})",
        db=db,
    )
