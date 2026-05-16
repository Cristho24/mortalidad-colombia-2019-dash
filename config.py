"""Configuration settings for the mortality analysis application."""

import os
from pathlib import Path
from typing import Dict, Any


class Config:
    """Base configuration class."""
    
    # Application settings
    APP_NAME = "Análisis de Mortalidad Colombia 2019"
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Server settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8050))
    
    # Data paths
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / 'data'
    
    # Data files
    MORTALITY_FILE = 'Anexo1.NoFetal2019_CE_15-03-23.xlsx'
    CODES_FILE = 'Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx'
    DIVIPOLA_FILE = 'Divipola_CE_.xlsx'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Performance
    WORKERS = int(os.getenv('WORKERS', 4))
    TIMEOUT = int(os.getenv('TIMEOUT', 120))
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get configuration as dictionary.
        
        Returns:
            Configuration dictionary
        """
        return {
            'app_name': cls.APP_NAME,
            'debug': cls.DEBUG,
            'host': cls.HOST,
            'port': cls.PORT,
            'data_dir': str(cls.DATA_DIR),
            'log_level': cls.LOG_LEVEL
        }


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = 'WARNING'


class AzureConfig(ProductionConfig):
    """Azure-specific configuration."""
    # Azure App Service sets PORT automatically
    PORT = int(os.getenv('PORT', 8000))
    
    # Azure-specific settings
    WEBSITE_HOSTNAME = os.getenv('WEBSITE_HOSTNAME', '')
    

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'azure': AzureConfig
}


def get_config(env: str = None) -> Config:
    """Get configuration based on environment.
    
    Args:
        env: Environment name (development, production, azure)
        
    Returns:
        Configuration class instance
    """
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    
    return config_map.get(env, DevelopmentConfig)
