from app.repositories.health_repository import HealthRepository
from app.schemas.health import HealthResponse


class HealthService:
    def __init__(self, repository: HealthRepository | None = None) -> None:
        self.repository = repository or HealthRepository()

    def get_health_response(self) -> HealthResponse:
        database_status = self.repository.get_database_status()
        return HealthResponse(status="ok", database=database_status)