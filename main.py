from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

from models.audit_log import AuditLog

from routes.auth import router as auth_router
from routes.events import router as events_router
from routes.venues import router as venues_router
from routes.speakers import router as speakers_router
from routes.sessions import router as sessions_router
from routes.registrations import router as registrations_router
from routes.tickets import router as tickets_router
from routes.purchases import router as purchases_router
from routes.payments import router as payments_router
from routes.session_bookings import router as session_bookings_router
from routes.checkins import router as checkins_router
from routes.certificates import router as certificates_router
from routes.feedback import router as feedback_router
from routes.notifications import router as notifications_router
from routes.refunds import router as refunds_router
from routes.dashboard import router as dashboard_router
from routes.reports import router as reports_router
from routes.audit_logs import router as audit_logs_router


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Event & Conference Management System API",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    auth_router,
    prefix="/api/v1",
)

app.include_router(
    events_router,
    prefix="/api/v1",
)

app.include_router(
    venues_router,
    prefix="/api/v1",
)

app.include_router(
    speakers_router,
    prefix="/api/v1",
)

app.include_router(
    sessions_router,
    prefix="/api/v1",
)

app.include_router(
    registrations_router,
    prefix="/api/v1",
)

app.include_router(
    tickets_router,
    prefix="/api/v1",
)

app.include_router(
    purchases_router,
    prefix="/api/v1",
)

app.include_router(
    payments_router,
    prefix="/api/v1",
)

app.include_router(
    session_bookings_router,
    prefix="/api/v1",
)

app.include_router(
    checkins_router,
    prefix="/api/v1",
)

app.include_router(
    certificates_router,
    prefix="/api/v1",
)

app.include_router(
    feedback_router,
    prefix="/api/v1",
)

app.include_router(
    notifications_router,
    prefix="/api/v1",
)

app.include_router(
    refunds_router,
    prefix="/api/v1",
)

app.include_router(
    dashboard_router,
    prefix="/api/v1",
)

app.include_router(
    reports_router,
    prefix="/api/v1",
)

app.include_router(
    audit_logs_router,
    prefix="/api/v1",
)


@app.get("/")
def root():
    return {
        "success": True,
        "message": "Event & Conference Management System API is running",
        "version": settings.APP_VERSION,
    }


@app.get("/health")
def health_check():
    return {
        "success": True,
        "status": "healthy",
    }