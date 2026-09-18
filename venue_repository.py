from sqlalchemy.orm import Session

from models.venue import Venue


class VenueRepository:

    @staticmethod
    def create(
        db: Session,
        venue: Venue,
    ) -> Venue:
        db.add(venue)
        db.commit()
        db.refresh(venue)
        return venue

    @staticmethod
    def get_by_id(
        db: Session,
        venue_id: int,
    ) -> Venue | None:
        return (
            db.query(Venue)
            .filter(Venue.id == venue_id)
            .first()
        )

    @staticmethod
    def get_all(
        db: Session,
    ) -> list[Venue]:
        return (
            db.query(Venue)
            .order_by(Venue.id.asc())
            .all()
        )