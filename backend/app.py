import os

from flask import Flask

from routers.assistant import assistant_router
from routers.health import health_router
from routers.routine import routine_router


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-memory-assistant-secret")

app.register_blueprint(health_router)
app.register_blueprint(assistant_router)
app.register_blueprint(routine_router)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
