# Dockerfile ל-Production
FROM python:3.11-slim

# הגדרת משתני סביבה
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# יצירת תיקיית עבודה
WORKDIR /app

# העתקת requirements והתקנת חבילות
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# העתקת כל הקבצים
COPY . .

# יצירת תיקיות נחוצות
RUN mkdir -p data_cache daily_results

# חשיפת פורט
EXPOSE 8501

# הגדרת בריאות (healthcheck)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8501/_stcore/health')" || exit 1

# הפעלת Streamlit
CMD ["streamlit", "run", "deltamix.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]

