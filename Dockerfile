# SPHEREx Motion Explorer — public web deployment image.
# The app queries NASA/IPAC IRSA live; no data is bundled or invented.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY frontend ./frontend

# Hugging Face Spaces / Render / Fly.io friendly: port via env, unprivileged user.
ENV PORT=7860 HOST=0.0.0.0
RUN useradd --create-home explorer && chown -R explorer:explorer /app
USER explorer

EXPOSE 7860
CMD ["sh", "-c", "python -m uvicorn backend.app:app --host ${HOST} --port ${PORT}"]
