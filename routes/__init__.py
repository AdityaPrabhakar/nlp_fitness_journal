# __init__.py

from .log_entry_routes import log_entry_bp
from .trend_routes import trend_bp
from .exercise_routes import exercise_bp
from .session_routes import session_bp
from .summary_routes import summary_bp

def register_routes(app):
    app.register_blueprint(log_entry_bp)
    app.register_blueprint(trend_bp)
    app.register_blueprint(exercise_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(summary_bp)


