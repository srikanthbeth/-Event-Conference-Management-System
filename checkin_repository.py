from sqlalchemy.orm import Session

from models.checkin import CheckIn


class CheckInRepository:

    @staticmethod
    def create(
        db: Session,
        check_in: CheckIn,
    ) -> CheckIn:

        db.add(check_in)
        db.commit()
        db.refresh(check_in)

        return check_in

    @staticmethod
    def get_by_id(
        db: Session,
        check_in_id: int,
    ) -> CheckIn | None:

        return (
            db.query(CheckIn)
            .filter(
                CheckIn.id == check_in_id,
            )
            .first()
        )

    @staticmethod
    def get_by_registration(
        db: Session,
        registration_id: int,
    ) -> CheckIn | None:

        return (
            db.query(CheckIn)
            .filter(
                CheckIn.registration_id == registration_id,
            )
            .first()
        )

    @staticmethod
    def get_by_event(
        db: Session,
        event_id: int,
    ):

        return (
            db.query(CheckIn)
            .join(
                CheckIn.registration,
            )
            .filter(
                CheckIn.registration.has(
                    event_id=event_id,
                )
            )
            .order_by(
                CheckIn.check_in_time.asc(),
            )
            .all()
        )

    @staticmethod
    def update(
        db: Session,
        check_in: CheckIn,
    ) -> CheckIn:

        db.commit()
        db.refresh(check_in)

        return check_in