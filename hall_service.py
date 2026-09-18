from sqlalchemy.orm import Session

from models.hall import Hall
from models.user import User
from repositories.hall_repository import HallRepository
from repositories.venue_repository import VenueRepository
from utils.enums import UserRole
from utils.exceptions import bad_request, forbidden, not_found


class HallService:

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
                "You do not have permission to manage halls"
            )

        if not current_user.is_active:
            raise forbidden(
                "Inactive users cannot manage halls"
            )

    @staticmethod
    def create_hall(
        db: Session,
        current_user: User,
        venue_id: int,
        hall_data,
    ) -> Hall:

        HallService._check_permission(
            current_user
        )

        venue = VenueRepository.get_by_id(
            db,
            venue_id,
        )

        if not venue:
            raise not_found(
                "Venue not found"
            )

        if hall_data.capacity > venue.capacity:
            raise bad_request(
                "Hall capacity cannot exceed venue capacity"
            )

        hall = Hall(
            venue_id=venue_id,
            hall_name=hall_data.hall_name,
            capacity=hall_data.capacity,
            floor=hall_data.floor,
            availability_status=(
                hall_data.availability_status
            ),
        )

        return HallRepository.create(
            db,
            hall,
        )

    @staticmethod
    def list_halls(
        db: Session,
        venue_id: int,
    ) -> list[Hall]:

        venue = VenueRepository.get_by_id(
            db,
            venue_id,
        )

        if not venue:
            raise not_found(
                "Venue not found"
            )

        return HallRepository.get_by_venue(
            db,
            venue_id,
        )