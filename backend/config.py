# backend/config.py - Environment Configuration & Validation

import os
import sys
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

class Settings:
    """Application settings with validation and defaults."""
    
    def __init__(self):
        self.validate_required_env_vars()
        self.setup_logging()
    
    # ============================================
    # REQUIRED ENVIRONMENT VARIABLES
    # ============================================
    
    @property
    def google_api_key(self) -> str:
        key = os.getenv("GOOGLE_API_KEY")
        if not key or key == "your_actual_google_maps_api_key_here":
            raise ValueError(
                "❌ GOOGLE_API_KEY is required!\n"
                "1. Get your API key from: https://console.cloud.google.com/\n"
                "2. Enable 'Geocoding API' and 'Maps JavaScript API'\n"
                "3. Set GOOGLE_API_KEY in your .env file"
            )
        return key
    
    @property
    def secret_key(self) -> str:
        key = os.getenv("SECRET_KEY")
        if not key or key == "your_super_secret_key_for_sessions_and_tokens":
            # Generate a random secret key for development
            import secrets
            key = secrets.token_urlsafe(32)
            logging.warning("⚠️  Using auto-generated SECRET_KEY. Set a permanent one in .env for production!")
        return key
    
    # ============================================
    # APPLICATION CONFIGURATION
    # ============================================
    
    @property
    def environment(self) -> str:
        return os.getenv("ENVIRONMENT", "development")
    
    @property
    def debug(self) -> bool:
        return os.getenv("DEBUG", "true").lower() == "true"
    
    @property
    def host(self) -> str:
        return os.getenv("HOST", "0.0.0.0")
    
    @property
    def port(self) -> int:
        return int(os.getenv("PORT", "8000"))
    
    @property
    def allowed_hosts(self) -> List[str]:
        hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
        return [host.strip() for host in hosts.split(",")]
    
    # ============================================
    # RATE LIMITING
    # ============================================
    
    @property
    def rate_limit_per_minute(self) -> int:
        return int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    
    @property
    def daily_quota_limit(self) -> int:
        return int(os.getenv("DAILY_QUOTA_LIMIT", "1000"))
    
    # ============================================
    # FILE STORAGE
    # ============================================
    
    @property
    def output_directory(self) -> Path:
        path = Path(os.getenv("OUTPUT_DIRECTORY", "./outputs"))
        path.mkdir(exist_ok=True)
        return path
    
    @property
    def max_file_size_mb(self) -> int:
        return int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    
    # ============================================
    # LOGGING
    # ============================================
    
    @property
    def log_level(self) -> str:
        return os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def log_file(self) -> Optional[str]:
        return os.getenv("LOG_FILE")
    
    # ============================================
    # VALIDATION METHODS
    # ============================================
    
    def validate_required_env_vars(self):
        """Validate that all required environment variables are set."""
        errors = []
        
        # Check Google API Key
        try:
            self.google_api_key
        except ValueError as e:
            errors.append(str(e))
        
        # Check for placeholder values
        placeholders = {
            "GOOGLE_API_KEY": "your_actual_google_maps_api_key_here",
            "SECRET_KEY": "your_super_secret_key_for_sessions_and_tokens",
        }
        
        for env_var, placeholder in placeholders.items():
            value = os.getenv(env_var)
            if value == placeholder:
                errors.append(f"❌ {env_var} still contains placeholder value. Please set a real value.")
        
        if errors:
            print("\n" + "="*60)
            print("🔑 ENVIRONMENT CONFIGURATION ERRORS")
            print("="*60)
            for error in errors:
                print(error)
            print("="*60)
            print("Please fix these issues and restart the application.")
            sys.exit(1)
    
    def setup_logging(self):
        """Configure application logging."""
        log_config = {
            'level': getattr(logging, self.log_level.upper()),
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
        
        if self.log_file:
            # Create log directory if it doesn't exist
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_config['filename'] = self.log_file
        
        logging.basicConfig(**log_config)
    
    def print_config_summary(self):
        """Print a summary of the current configuration."""
        print("\n" + "="*60)
        print("🚀 APPLICATION CONFIGURATION")
        print("="*60)
        print(f"Environment: {self.environment}")
        print(f"Debug Mode: {self.debug}")
        print(f"Host: {self.host}:{self.port}")
        print(f"Output Directory: {self.output_directory}")
        print(f"Rate Limit: {self.rate_limit_per_minute}/min")
        print(f"Daily Quota: {self.daily_quota_limit}")
        print(f"Log Level: {self.log_level}")
        print(f"Google API Key: {'✅ Configured' if self.google_api_key else '❌ Missing'}")
        print("="*60)

# Global settings instance
settings = Settings()

# Validation function for startup
def validate_environment():
    """Validate environment on application startup."""
    try:
        settings.validate_required_env_vars()
        if settings.debug:
            settings.print_config_summary()
        return True
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        return False
