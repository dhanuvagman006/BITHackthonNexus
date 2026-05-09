DEPENDENCIES = {
    "database": [],
    "auth_service": ["database"],
    "backend_api": ["auth_service"],
    "frontend": ["backend_api"]
}