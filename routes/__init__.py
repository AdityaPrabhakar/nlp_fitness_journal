# __init__.py
from .log_entry_routes import log_entry_bp
from .progress_routes import progress_bp
from .exercise_routes import exercise_bp

def register_routes(app):
    app.register_blueprint(log_entry_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(exercise_bp)


