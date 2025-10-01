"""Reflex configuration file for Water Quality Monitoring Application"""

import reflex as rx
import os

# Get version type
VERSION_TYPE = os.getenv("VERSION_TYPE", "RPI").upper()

config = rx.Config(
    app_name="water_app",

    # Port configuration (different for RPI vs CPS to allow simultaneous running)
    frontend_port=13000 if VERSION_TYPE == "RPI" else 13100,
    backend_port=13001 if VERSION_TYPE == "RPI" else 13101,

    # API URL
    api_url="http://localhost:13000" if VERSION_TYPE == "RPI" else "http://localhost:13100",

    # Backend host
    backend_host="0.0.0.0",

    # Database
    db_url=os.getenv("TS_DSN", "postgresql://water_user:water_password@localhost:5432/water_db"),

    # Environment
    env=rx.Env.DEV if os.getenv("ENVIRONMENT", "development") == "development" else rx.Env.PROD,

    # Telemetry
    telemetry_enabled=False,
)
