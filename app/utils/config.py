"""Configuration management for the Fantasy Football Agent."""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google Gemini API
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    
    # Yahoo Fantasy Football API
    yahoo_consumer_key: Optional[str] = Field(None, env="YAHOO_CONSUMER_KEY")
    yahoo_consumer_secret: Optional[str] = Field(None, env="YAHOO_CONSUMER_SECRET")
    yahoo_league_id: Optional[str] = Field(None, env="YAHOO_LEAGUE_ID")
    yahoo_game_id: int = Field(449, env="YAHOO_GAME_ID")  # NFL default
    
    # Yahoo OAuth Tokens (for MCP server)
    yahoo_access_token: Optional[str] = Field(None, env="YAHOO_ACCESS_TOKEN")
    yahoo_refresh_token: Optional[str] = Field(None, env="YAHOO_REFRESH_TOKEN")
    yahoo_guid: Optional[str] = Field(None, env="YAHOO_GUID")
    
    # Yahoo Account (for browser automation)
    yahoo_email: Optional[str] = Field(None, env="YAHOO_EMAIL")
    yahoo_password: Optional[str] = Field(None, env="YAHOO_PASSWORD")
    
    # ADK Configuration
    adk_project_id: str = Field("football-agent", env="ADK_PROJECT_ID")
    adk_region: str = Field("us-central1", env="ADK_REGION")
    
    # ADK Web Server Port
    adk_web_port: int = Field(8080, env="ADK_WEB_PORT")
    
    # MCP Server URLs (for HTTP transport if needed)
    # Note: MCP servers use stdio by default, these are only for HTTP transport
    mcp_yahoo_server_url: str = Field("http://localhost:8001", env="MCP_YAHOO_SERVER_URL")
    mcp_browser_server_url: str = Field("http://localhost:8002", env="MCP_BROWSER_SERVER_URL")
    
    # Model configuration
    # Using gemini-2.5-pro for function calling support (required for ADK FunctionTools)
    model_name: str = Field("gemini-2.5-pro", env="MODEL_NAME")
    temperature: float = Field(0.7, env="TEMPERATURE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

