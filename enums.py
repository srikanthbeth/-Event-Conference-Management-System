from enum import Enum


class UserRole(str, Enum):
    ADMIN = "Admin"
    EVENT_ORGANIZER = "Event Organizer"
    SPEAKER = "Speaker"
    STAFF = "Staff"
    ATTENDEE = "Attendee"


class EventType(str, Enum):
    CONFERENCE = "Conference"
    WORKSHOP = "Workshop"
    SEMINAR = "Seminar"
    MEETUP = "Meetup"
    TRAINING = "Training"


class EventStatus(str, Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"
    REGISTRATION_OPEN = "Registration Open"
    REGISTRATION_CLOSED = "Registration Closed"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class VenueStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class HallAvailabilityStatus(str, Enum):
    AVAILABLE = "Available"
    UNAVAILABLE = "Unavailable"


class RegistrationStatus(str, Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"
    ATTENDED = "Attended"


class TicketType(str, Enum):
    STANDARD = "Standard"
    VIP = "VIP"
    EARLY_BIRD = "Early Bird"
    STUDENT = "Student"

class PaymentMethod(str, Enum):
    UPI = "UPI"
    CARD = "Card"
    WALLET = "Wallet"
    CASH = "Cash"


class PaymentStatus(str, Enum):
    PENDING = "Pending"
    SUCCESSFUL = "Successful"
    FAILED = "Failed"



class SessionBookingStatus(str, Enum):
    BOOKED = "Booked"
    CANCELLED = "Cancelled"

class CheckInMethod(str, Enum):
    QR_CODE = "QR Code"
    MANUAL = "Manual"
    STAFF = "Staff"


class CertificateType(str, Enum):
    PARTICIPATION = "Participation"
    COMPLETION = "Completion"
    SPEAKER = "Speaker"


class CertificateStatus(str, Enum):
    ISSUED = "Issued"
    REVOKED = "Revoked"


class RefundStatus(str, Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"