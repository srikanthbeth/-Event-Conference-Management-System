from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.hall import HallCreate, HallResponse
from schemas.venue import VenueCreate, VenueResponse
from services.hall_service import HallService
from services.venue_service import VenueService
from utils.dependencies import get_current_user


router = APIRouter(
    prefix="/venues",
    tags=["Venues"],
)


@router.post(
    "",
    response_model=VenueResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_venue(
    venue_data: VenueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return VenueService.create_venue(
        db,
        current_user,
        venue_data,
    )


@router.get(
    "",
    response_model=list[VenueResponse],
)
def list_venues(
    db: Session = Depends(get_db),
):
    return VenueService.list_venues(db)


@router.post(
    "/{venue_id}/halls",
    response_model=HallResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_hall(
    venue_id: int,
    hall_data: HallCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return HallService.create_hall(
        db,
        current_user,
        venue_id,
        hall_data,
    )


@router.get(
    "/{venue_id}/halls",
    response_model=list[HallResponse],
)
def list_halls(
    venue_id: int,
    db: Session = Depends(get_db),
):
    return HallService.list_halls(
        db,
        venue_id,
    )