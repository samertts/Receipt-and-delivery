from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.container_deps import get_organization_service
from app.api.deps import require_permission
from app.core.response_envelope import paginated_response
from app.db.session import get_db
from app.models.user import User
from app.schemas.transaction import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)

router = APIRouter(prefix="/organizations", tags=["المؤسسات"])


@router.get("")
def list_organizations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    _active_only: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("view_organizations")),
):
    svc = get_organization_service(db)
    items, total = svc.list_organizations(page=page, limit=limit)
    return paginated_response(
        items=[OrganizationResponse.model_validate(o).model_dump(mode="json") for o in items],
        total=total,
        page=page,
        per_page=limit,
    )


@router.post("", response_model=OrganizationResponse, status_code=201)
def create_organization(
    payload: OrganizationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_organizations")),
):
    svc = get_organization_service(db)
    return svc.create_organization(
        name=payload.name,
        code=payload.code,
        address=payload.address or "",
        phone=payload.phone or "",
        email=payload.email or "",
        logo_path=payload.logo_path or "",
        request=request,
        current_user=current_user,
    )


@router.get("/{org_id}", response_model=OrganizationResponse)
def get_organization(
    org_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("view_organizations")),
):
    svc = get_organization_service(db)
    return svc.get_organization(org_id)


@router.put("/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: str,
    payload: OrganizationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_organizations")),
):
    svc = get_organization_service(db)
    return svc.update_organization(
        org_id,
        name=payload.name,
        code=payload.code,
        address=payload.address,
        phone=payload.phone,
        email=payload.email,
        request=request,
        current_user=current_user,
    )


@router.delete("/{org_id}", status_code=204)
def delete_organization(
    org_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_organizations")),
):
    svc = get_organization_service(db)
    svc.delete_organization(org_id, request=request, current_user=current_user)
