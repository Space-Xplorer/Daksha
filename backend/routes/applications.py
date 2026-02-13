"""
Application management routes for Daksha API.

This module handles CRUD operations for loan and insurance applications.
"""

import logging
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

logger = logging.getLogger(__name__)

bp = Blueprint('applications', __name__)

# In-memory application store (replace with database in production)
applications_db = {}


@bp.route('/', methods=['POST'])
@jwt_required()
def create_application():
    """
    Create a new loan/insurance application.
    
    Request Body:
        {
            "request_type": "loan" | "insurance" | "both",
            "loan_type": "home" | "personal" | "auto" (if loan),
            "submitted_name": "Applicant Name",
            "submitted_dob": "YYYY-MM-DD",
            "applicant_data": {
                // Loan fields
                "cibil_score": 750,
                "annual_income": 1200000,
                "loan_amount": 500000,
                "existing_debt": 100000,
                "employment_type": "salaried",
                "employment_years": 5,
                
                // Insurance fields
                "age": 32,
                "bmi": 24.5,
                "smoker": false,
                "pre_existing_conditions": [],
                ...
            }
        }
    
    Returns:
        201: Application created
        400: Invalid input
    """
    try:
        user_email = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('request_type'):
            return jsonify({'error': 'request_type is required'}), 400
        
        if data['request_type'] not in ['loan', 'insurance', 'both']:
            return jsonify({'error': 'Invalid request_type'}), 400
        
        # Create application
        app_id = str(uuid.uuid4())
        application = {
            'id': app_id,
            'user_email': user_email,
            'request_type': data['request_type'],
            'loan_type': data.get('loan_type'),
            'submitted_name': data.get('submitted_name', ''),
            'submitted_dob': data.get('submitted_dob', ''),
            'submitted_aadhaar': data.get('submitted_aadhaar', ''),
            'applicant_data': data.get('applicant_data', {}),
            'uploaded_documents': data.get('uploaded_documents', []),
            'status': 'draft',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        applications_db[app_id] = application
        
        logger.info(f"Application created: {app_id} by {user_email}")
        
        return jsonify({
            'message': 'Application created successfully',
            'application': application
        }), 201
        
    except Exception as e:
        logger.error(f"Create application error: {e}")
        return jsonify({'error': 'Failed to create application'}), 500


@bp.route('/', methods=['GET'])
@jwt_required()
def list_applications():
    """
    List all applications for the current user.
    
    Query Parameters:
        status: Filter by status (optional)
        request_type: Filter by request type (optional)
    
    Returns:
        200: List of applications
    """
    try:
        user_email = get_jwt_identity()
        status_filter = request.args.get('status')
        type_filter = request.args.get('request_type')
        
        # Filter applications
        user_apps = [
            app for app in applications_db.values()
            if app['user_email'] == user_email
        ]
        
        if status_filter:
            user_apps = [app for app in user_apps if app['status'] == status_filter]
        
        if type_filter:
            user_apps = [app for app in user_apps if app['request_type'] == type_filter]
        
        # Sort by created_at descending
        user_apps.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'applications': user_apps,
            'count': len(user_apps)
        }), 200
        
    except Exception as e:
        logger.error(f"List applications error: {e}")
        return jsonify({'error': 'Failed to list applications'}), 500


@bp.route('/<app_id>', methods=['GET'])
@jwt_required()
def get_application(app_id):
    """
    Get a specific application by ID.
    
    Returns:
        200: Application details
        404: Application not found
        403: Forbidden (not owner)
    """
    try:
        user_email = get_jwt_identity()
        
        application = applications_db.get(app_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Check ownership
        if application['user_email'] != user_email:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'application': application}), 200
        
    except Exception as e:
        logger.error(f"Get application error: {e}")
        return jsonify({'error': 'Failed to get application'}), 500


@bp.route('/<app_id>', methods=['PUT'])
@jwt_required()
def update_application(app_id):
    """
    Update an existing application.
    
    Request Body:
        {
            "applicant_data": {...},
            "submitted_name": "...",
            ...
        }
    
    Returns:
        200: Application updated
        404: Application not found
        403: Forbidden (not owner)
    """
    try:
        user_email = get_jwt_identity()
        data = request.get_json()
        
        application = applications_db.get(app_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Check ownership
        if application['user_email'] != user_email:
            return jsonify({'error': 'Access denied'}), 403
        
        # Update fields
        if 'applicant_data' in data:
            application['applicant_data'].update(data['applicant_data'])
        if 'submitted_name' in data:
            application['submitted_name'] = data['submitted_name']
        if 'submitted_dob' in data:
            application['submitted_dob'] = data['submitted_dob']
        if 'submitted_aadhaar' in data:
            application['submitted_aadhaar'] = data['submitted_aadhaar']
        if 'uploaded_documents' in data:
            application['uploaded_documents'] = data['uploaded_documents']
        
        application['updated_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"Application updated: {app_id}")
        
        return jsonify({
            'message': 'Application updated successfully',
            'application': application
        }), 200
        
    except Exception as e:
        logger.error(f"Update application error: {e}")
        return jsonify({'error': 'Failed to update application'}), 500


@bp.route('/<app_id>', methods=['DELETE'])
@jwt_required()
def delete_application(app_id):
    """
    Delete an application.
    
    Returns:
        200: Application deleted
        404: Application not found
        403: Forbidden (not owner)
    """
    try:
        user_email = get_jwt_identity()
        
        application = applications_db.get(app_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Check ownership
        if application['user_email'] != user_email:
            return jsonify({'error': 'Access denied'}), 403
        
        del applications_db[app_id]
        
        logger.info(f"Application deleted: {app_id}")
        
        return jsonify({'message': 'Application deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Delete application error: {e}")
        return jsonify({'error': 'Failed to delete application'}), 500
