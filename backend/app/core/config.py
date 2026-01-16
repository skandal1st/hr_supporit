from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "HR-IT Lifecycle Manager"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60 * 12
    database_url: str = "sqlite:///./hr_desk.db"
    supporit_api_url: str | None = None
    supporit_token: str | None = None
    supporit_timeout_seconds: int = 10
    ad_server: str | None = None
    ad_user: str | None = None
    ad_password: str | None = None
    ad_base_dn: str | None = None
    ad_domain: str | None = None
    ad_use_ssl: bool = True
    ad_timeout_seconds: int = 10
    mailcow_api_url: str | None = None
    mailcow_api_key: str | None = None
    zup_api_url: str | None = None
    zup_username: str | None = None
    zup_password: str | None = None
    zup_webhook_token: str | None = None  # Токен для аутентификации webhook от 1С
    seed_admin_enabled: bool = True
    seed_admin_email: str = "utkin@teplocentral.org"
    seed_admin_password: str = "23solomon7"
    seed_admin_role: str = "admin"


settings = Settings()
