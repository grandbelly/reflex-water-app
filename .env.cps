# CPS Version Environment Variables
# Full-featured with AI Insights and SCADA Alarms

# ============================================================================
# VERSION CONTROL
# ============================================================================
VERSION_TYPE=CPS
ENABLE_AI_FEATURES=true

# ============================================================================
# APPLICATION
# ============================================================================
ENVIRONMENT=production
TZ=Asia/Seoul

# ============================================================================
# DATABASE
# ============================================================================
TS_DSN=postgresql://water_user:water_password@cps-db:5432/water_db

# ============================================================================
# PORTS (CPS uses 13100-13101)
# ============================================================================
FRONTEND_PORT=13100
BACKEND_PORT=13101

# ============================================================================
# AI/ML CONFIGURATION (CPS Only)
# ============================================================================
OPENAI_API_KEY=sk-your-api-key-here
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Ollama Configuration
OLLAMA_HOST=http://cps-ollama:11434
OLLAMA_MODEL=nomic-embed-text
