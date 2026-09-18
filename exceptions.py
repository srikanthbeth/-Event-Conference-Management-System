from fastapi import HTTPException, status


def unauthorized(message: str = "Invalid authentication credentials"):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden(message: str = "You do not have permission to perform this action"):
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=message,
    )


def not_found(message: str = "Resource not found"):
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=message,
    )


def bad_request(message: str):
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message,
    )