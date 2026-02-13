"""
Flask application factory for Daksha API.

This module creates and configures the Flask application with all necessary
extensions, middleware, and route blueprints.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

from routes import auth, applications, workflow, admin
from middleware.error_handler import register_error_handlers
from src.utils.logging import setup_logging

# Load environment variables
load_dotenv()


def create_app(config=None):
    """
    Create and configure the Flask application.
    
    Args:
        config: Optional configuration dictionary
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # 1 hour
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000  # 30 days
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload
    
    # Apply custom config if provided
    if config:
        app.config.update(config)
    
    # Initialize extensions
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    jwt = JWTManager(app)
    
    # Setup logging
    setup_logging("INFO", "daksha_api.log", True)
    
    # Register blueprints
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(applications.bp, url_prefix='/api/applications')
    app.register_blueprint(workflow.bp, url_prefix='/api/workflow')
    app.register_blueprint(admin.bp, url_prefix='/api/admin')
    
    # Register error handlers
    register_error_handlers(app)
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint for monitoring."""
        return jsonify({
            'status': 'healthy',
            'service': 'Daksha API',
            'version': '1.0.0'
        }), 200
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        """Root endpoint with API information."""
        return jsonify({
            'service': 'Daksha Orchestration System API',
            'version': '1.0.0',
            'documentation': '/api/docs',
            'health': '/api/health'
        }), 200
    
    return app


if __name__ == '__main__':
    # Create app
    app = create_app()
    
    # Get configuration from environment
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║              DAKSHA API SERVER STARTING                  ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    
    🚀 Server running at: http://{host}:{port}
    📚 API Documentation: backend/API_DOCUMENTATION.md
    🏥 Health Check: http://{host}:{port}/api/health
    
    Default Admin Credentials:
    📧 Email: admin@daksha.com
    🔑 Password: admin123
    
    Press CTRL+C to stop the server
    """)
    
    # Run server
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )
