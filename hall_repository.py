from sqlalchemy.orm import Session

from models.hall import Hall


class HallRepository:

    @staticmethod
    def create(
        db: Session,
        hall: Hall,
    ) -> Hall:
        db.add(hall)
        db.commit()
        db.refresh(hall)
        return hall

    @staticmethod
    def get_by_venue(
        db: Session,
        venue_id: int,
    ) -> list[Hall]:
        return (
            db.query(Hall)
            .filter(Hall.venue_id == venue_id)
            .order_by(Hall.id.asc())
            .all()
        )