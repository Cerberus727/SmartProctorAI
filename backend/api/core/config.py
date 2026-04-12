from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Proctoring API"
    SECRET_KEY: str = "your-super-secret-key-change-it"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    # You can easily change this to PostgreSQL: postgresql://user:password@localhost/dbname
    DATABASE_URL: str = "sqlite:///./exam.db"
    
    class Config:
        env_file = ".env"

settings = Settings()
