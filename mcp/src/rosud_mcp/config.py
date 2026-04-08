"""Rosud MCP Server configuration"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    rosud_api_key: str = ""
    rosud_api_url: str = "https://api.rosud.com"

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
