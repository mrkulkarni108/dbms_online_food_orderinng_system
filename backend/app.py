from pathlib import Path

from flask import Flask, flash, redirect, render_template, session, url_for
from mysql.connector import Error as MySQLError

from config.config import get_config
from routes.auth_routes import auth_bp
from routes.order_routes import order_bp
from routes.profile_routes import profile_bp
from services.database_service import DatabaseServiceError, init_db
from utils.logger import configure_logging
from utils.validation_helper import ValidationError

BASE_DIR = Path(__file__).resolve().parents[1]


def create_app():
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / 'templates'),
        static_folder=str(BASE_DIR / 'static'),
    )
    app.config.from_object(get_config())
    configure_logging(app)

    if app.config['APP_ENV'] == 'production' and app.config['SECRET_KEY'] == 'change-this-in-production':
        raise RuntimeError('Production secret key is not configured.')
    if app.config['APP_ENV'] == 'production' and not app.config['DB_PASSWORD']:
        raise RuntimeError('Production database password is not configured.')

    try:
        init_db()
    except DatabaseServiceError:
        app.logger.exception('Application startup failed during database initialization.')
        raise

    @app.route('/')
    def home():
        return render_template('index.html')

    @app.context_processor
    def inject_navigation_state():
        return {
            'logged_in': bool(session.get('user_id')),
        }

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        flash(str(error), 'error')
        app.logger.warning('Validation error: %s', error)
        return redirect(url_for('home'))

    @app.errorhandler(DatabaseServiceError)
    @app.errorhandler(MySQLError)
    def handle_database_error(error):
        app.logger.exception('Database error: %s', error)
        return render_template(
            'error.html',
            title='Database Issue',
            message='The service is temporarily unavailable. Please try again shortly.',
        ), 500

    @app.errorhandler(404)
    def handle_not_found(error):
        return render_template(
            'error.html',
            title='Page Not Found',
            message='The page you are looking for does not exist or may have moved.',
        ), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception('Unhandled application error: %s', error)
        return render_template(
            'error.html',
            title='Something Went Wrong',
            message='We hit an unexpected problem. Our team has been notified.',
        ), 500

    app.register_blueprint(auth_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(profile_bp)
    app.logger.info('Application created successfully.')
    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
