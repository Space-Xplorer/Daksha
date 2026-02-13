"""
Admin routes for Daksha API.

This module provides administrative endpoints for system monitoring and management.
"""

import logging
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from functools import wraps

from routes.applications import applications_db
from routes.workflow import workflow_executions

logger = logging.getLogger(__name__)

bp = Blueprint('admin', __name__)


def admin_required():
    """Decorator to require admin role."""
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper


@bp.route('/stats', methods=['GET'])
@admin_required()
def get_system_stats():
    """
    Get system statistics.
    
    Returns:
        200: System statistics
    """
    try:
        # Calculate stats
        total_applications = len(applications_db)
        
        status_counts = {}
        type_counts = {}
        
        for app in applications_db.values():
            status = app['status']
            status_counts[status] = status_counts.get(status, 0) + 1
            
            req_type = app['request_type']
            type_counts[req_type] = type_counts.get(req_type, 0) + 1
        
        workflow_status_counts = {}
        for execution in workflow_executions.values():
            status = execution['status']
            workflow_status_counts[status] = workflow_status_counts.get(status, 0) + 1
        
        return jsonify({
            'applications': {
                'total': total_applications,
                'by_status': status_counts,
                'by_type': type_counts
            },
            'workflows': {
                'total': len(workflow_executions),
                'by_status': workflow_status_counts
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get system stats error: {e}")
        return jsonify({'error': 'Failed to get system stats'}), 500


@bp.route('/applications', methods=['GET'])
@admin_required()
def list_all_applications():
    """
    List all applications (admin only).
    
    Returns:
        200: List of all applications
    """
    try:
        all_apps = list(applications_db.values())
        all_apps.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'applications': all_apps,
            'count': len(all_apps)
        }), 200
        
    except Exception as e:
        logger.error(f"List all applications error: {e}")
        return jsonify({'error': 'Failed to list applications'}), 500


@bp.route('/workflows', methods=['GET'])
@admin_required()
def list_all_workflows():
    """
    List all workflow executions (admin only).
    
    Returns:
        200: List of all workflow executions
    """
    try:
        all_workflows = list(workflow_executions.values())
        
        return jsonify({
            'workflows': all_workflows,
            'count': len(all_workflows)
        }), 200
        
    except Exception as e:
        logger.error(f"List all workflows error: {e}")
        return jsonify({'error': 'Failed to list workflows'}), 500
