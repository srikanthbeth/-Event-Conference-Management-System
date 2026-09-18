from datetime import datetime

from pydantic import BaseModel, ConfigDict

from utils.enums import CheckInMethod


class CheckInResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    registration_id: int
    check_in_time: datetime
    check_out_time: datetime | None
    check_in_method: CheckInMethod