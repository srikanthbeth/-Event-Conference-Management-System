from sqlalchemy.orm import Session

from models.user import User
from models.venue import Venue
from repositories.venue_repository import VenueRepository
from utils.enums import UserRole
from utils.exceptions import forbidden


class VenueService:

    @staticmethod
    def _check_permission(
        current_user: User,
    ) -> None:

        if current_user.role not in (
            UserRole.ADMIN,
            UserRole.EVENT_ORGANIZER,
            UserRole.STAFF,
        ):
            raise forbidden(
                "You do not have permission to manage venues"
            )

        if not current_user.is_active:
            raise forbidden(
                "Inactive users cannot manage venues"
            )

    @staticmethod
    def create_venue(
        db: Session,
        current_user: User,
        venue_data,
    ) -> Venue:

        VenueService._check_permission(
            current_user
        )

        venue = Venue(
            venue_name=venue_data.venue_name,
            address=venue_data.address,
            city=venue_data.city,
            capacity=venue_data.capacity,
            facilities=venue_data.facilities,
            status=venue_data.status,
        )

        return VenueRepository.create(
            db,
            venue,
        )

    @staticmethod
    def list_venues(
        db: Session,
    ) -> list[Venue]:

        return VenueRepository.get_all(db)