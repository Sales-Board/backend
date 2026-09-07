from app.db.database import check_database_connection


class HealthRepository:
    def get_database_status(self) -> str:
        return check_database_connection()