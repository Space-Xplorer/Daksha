"""
Workflow execution routes for Daksha API.

This module handles workflow execution, status tracking, and HITL interactions.
"""

import base64
import logging
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.schemas.state import create_initial_state
from routes.applications import applications_db

logger = logging.getLogger(__name__)

bp = Blueprint('workflow', __name__)

# Thread pool for async execution
executor = ThreadPoolExecutor(max_workers=4)

# Workflow execution store
workflow_executions = {}


def get_run_workflow():
    """
    Lazy import of run_workflow to avoid loading agents at module import time.
    This allows .env to be loaded first.
    """
    from src.graph.workflow import run_workflow
    return run_workflow


def run_workflow_async(state):
    """
    Run workflow in a separate thread.
    
    Args:
        state: Initial application state
    
    Returns:
        Final state after workflow execution
    """
    try:
        run_workflow = get_run_workflow()
        return run_workflow(state)
    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        raise


def _materialize_uploaded_documents(app_id: str, uploaded_documents):
    if not uploaded_documents:
        return []

    output_dir = Path("temp") / "uploads" / app_id
    output_dir.mkdir(parents=True, exist_ok=True)

    mime_extensions = {
        "application/pdf": ".pdf",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png"
    }

    materialized = []
    for index, doc in enumerate(uploaded_documents, start=1):
        doc_type = doc.get("type") or doc.get("document_type") or "unknown"
        name = doc.get("name") or f"{doc_type}_{index}"
        content_base64 = doc.get("content_base64")
        file_path = doc.get("file_path")

        if content_base64:
            ext = Path(name).suffix
            if not ext:
                ext = mime_extensions.get(doc.get("mime_type"), ".pdf")

            safe_name = f"{doc_type}_{index}{ext}"
            target_path = output_dir / safe_name

            try:
                decoded = base64.b64decode(content_base64)
                target_path.write_bytes(decoded)
                file_path = str(target_path)
            except Exception as exc:
                logger.error(f"Failed to write uploaded document {name}: {exc}")
                continue

        if file_path:
            materialized.append({
                "type": doc_type,
                "file_path": file_path,
                "name": name
            })

    return materialized


@bp.route('/submit/<app_id>', methods=['POST'])
@jwt_required()
def submit_application(app_id):
    """
    Submit an application for workflow processing.
    
    This starts the Daksha workflow: KYC → Onboarding → HITL → Compliance → 
    Router → Underwriting → Verification → Transparency → Supervisor
    
    Returns:
        202: Workflow started (async)
        404: Application not found
        403: Forbidden (not owner)
        400: Application already submitted
    """
    try:
        user_email = get_jwt_identity()
        
        # Get application
        application = applications_db.get(app_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Check ownership
        if application['user_email'] != user_email:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if already submitted
        if application['status'] != 'draft':
            return jsonify({'error': 'Application already submitted'}), 400
        
        # Create initial state
        uploaded_documents = _materialize_uploaded_documents(
            app_id,
            application.get("uploaded_documents", [])
        )

        state = create_initial_state(
            request_type=application['request_type'],
            applicant_data=application['applicant_data'],
            loan_type=application.get('loan_type'),
            submitted_name=application.get('submitted_name'),
            submitted_dob=application.get('submitted_dob'),
            submitted_aadhaar=application.get('submitted_aadhaar'),
            uploaded_documents=uploaded_documents
        )
        
        # Update application status
        application['status'] = 'processing'
        application['request_id'] = state['request_id']
        
        # Store execution
        workflow_executions[app_id] = {
            'app_id': app_id,
            'request_id': state['request_id'],
            'status': 'running',
            'current_state': state,
            'started_at': state['timestamp']
        }
        
        # Start workflow asynchronously
        future = executor.submit(run_workflow_async, state)
        
        def workflow_callback(fut):
            """Callback when workflow completes."""
            try:
                final_state = fut.result()
                workflow_executions[app_id]['status'] = 'completed'
                workflow_executions[app_id]['current_state'] = final_state
                application['status'] = 'completed'
                application['final_state'] = final_state
                logger.info(f"Workflow completed for application: {app_id}")
            except Exception as e:
                logger.error(f"Workflow failed for application {app_id}: {e}")
                workflow_executions[app_id]['status'] = 'failed'
                workflow_executions[app_id]['error'] = str(e)
                application['status'] = 'failed'
        
        future.add_done_callback(workflow_callback)
        
        logger.info(f"Workflow started for application: {app_id}")
        
        return jsonify({
            'message': 'Workflow started',
            'app_id': app_id,
            'request_id': state['request_id'],
            'status': 'processing'
        }), 202
        
    except Exception as e:
        logger.error(f"Submit application error: {e}")
        return jsonify({'error': 'Failed to submit application'}), 500


@bp.route('/status/<app_id>', methods=['GET'])
@jwt_required()
def get_workflow_status(app_id):
    """
    Get workflow execution status for an application.
    
    Returns:
        200: Workflow status
        404: Workflow not found
    """
    try:
        user_email = get_jwt_identity()
        
        # Check application ownership
        application = applications_db.get(app_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        if application['user_email'] != user_email:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get workflow execution
        execution = workflow_executions.get(app_id)
        if not execution:
            return jsonify({'error': 'Workflow not found'}), 404
        
        # Build response
        response = {
            'app_id': app_id,
            'request_id': execution['request_id'],
            'status': execution['status'],
            'started_at': execution['started_at']
        }
        
        # Add current state info
        state = execution['current_state']
        response['kyc_verified'] = state.get('kyc_verified', False)
        response['compliance_passed'] = state.get('compliance_passed', False)
        response['hitl_checkpoint'] = state.get('hitl_checkpoint', False)
        
        # Add results if completed
        if execution['status'] == 'completed':
            response['loan_prediction'] = state.get('loan_prediction')
            response['insurance_prediction'] = state.get('insurance_prediction')
            response['loan_explanation'] = state.get('loan_explanation')
            response['insurance_explanation'] = state.get('insurance_explanation')
            response['supervisor_decision'] = state.get('supervisor_decision')
        
        # Add error if failed
        if execution['status'] == 'failed':
            response['error'] = execution.get('error')
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Get workflow status error: {e}")
        return jsonify({'error': 'Failed to get workflow status'}), 500


@bp.route('/results/<app_id>', methods=['GET'])
@jwt_required()
def get_workflow_results(app_id):
    """
    Get complete workflow results for a completed application.
    
    Returns:
        200: Complete workflow results
        404: Application not found
        400: Workflow not completed
    """
    try:
        user_email = get_jwt_identity()
        
        # Check application ownership
        application = applications_db.get(app_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        if application['user_email'] != user_email:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if workflow completed
        if application['status'] != 'completed':
            return jsonify({'error': 'Workflow not completed yet'}), 400
        
        final_state = application.get('final_state', {})
        
        return jsonify({
            'app_id': app_id,
            'request_id': final_state.get('request_id'),
            'request_type': final_state.get('request_type'),
            
            # KYC Results
            'kyc': {
                'verified': final_state.get('kyc_verified', False),
                'verified_name': final_state.get('verified_name'),
                'verified_dob': final_state.get('verified_dob'),
                'digilocker_id': final_state.get('digilocker_id')
            },
            
            # Compliance Results
            'compliance': {
                'passed': final_state.get('compliance_passed', False),
                'violations': final_state.get('compliance_violations', [])
            },
            
            # Loan Results
            'loan': {
                'prediction': final_state.get('loan_prediction'),
                'explanation': final_state.get('loan_explanation'),
                'verification': final_state.get('loan_verification')
            } if final_state.get('loan_prediction') else None,
            
            # Insurance Results
            'insurance': {
                'prediction': final_state.get('insurance_prediction'),
                'explanation': final_state.get('insurance_explanation'),
                'verification': final_state.get('insurance_verification')
            } if final_state.get('insurance_prediction') else None,
            
            # Supervisor Decision
            'supervisor': final_state.get('supervisor_decision'),
            
            # Errors
            'errors': final_state.get('errors', []),
            
            # Metadata
            'completed': final_state.get('completed', False),
            'timestamp': final_state.get('timestamp')
        }), 200
        
    except Exception as e:
        logger.error(f"Get workflow results error: {e}")
        return jsonify({'error': 'Failed to get workflow results'}), 500


@bp.route('/hitl/<app_id>', methods=['GET'])
@jwt_required()
def get_hitl_data(app_id):
    """
    Get HITL checkpoint data for review.
    
    Returns:
        200: HITL data for review
        404: Application not found
        400: Not at HITL checkpoint
    """
    try:
        user_email = get_jwt_identity()
        
        # Check application ownership
        application = applications_db.get(app_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        if application['user_email'] != user_email:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get workflow execution
        execution = workflow_executions.get(app_id)
        if not execution:
            return jsonify({'error': 'Workflow not found'}), 404
        
        state = execution['current_state']
        
        # Check if at HITL checkpoint
        if not state.get('hitl_checkpoint'):
            return jsonify({'error': 'Not at HITL checkpoint'}), 400
        
        return jsonify({
            'app_id': app_id,
            'extracted_data': state.get('extracted_data', {}),
            'applicant_data': state.get('applicant_data', {}),
            'documents_processed': state.get('documents_processed', [])
        }), 200
        
    except Exception as e:
        logger.error(f"Get HITL data error: {e}")
        return jsonify({'error': 'Failed to get HITL data'}), 500


@bp.route('/hitl/<app_id>/approve', methods=['POST'])
@jwt_required()
def approve_hitl(app_id):
    """
    Approve HITL checkpoint and continue workflow.
    
    Request Body:
        {
            "corrections": {
                "field_name": "corrected_value",
                ...
            }
        }
    
    Returns:
        200: HITL approved, workflow continuing
        404: Application not found
        400: Not at HITL checkpoint
    """
    try:
        user_email = get_jwt_identity()
        data = request.get_json() or {}
        
        # Check application ownership
        application = applications_db.get(app_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        if application['user_email'] != user_email:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get workflow execution
        execution = workflow_executions.get(app_id)
        if not execution:
            return jsonify({'error': 'Workflow not found'}), 404
        
        state = execution['current_state']
        
        # Check if at HITL checkpoint
        if not state.get('hitl_checkpoint'):
            return jsonify({'error': 'Not at HITL checkpoint'}), 400
        
        # Apply corrections
        corrections = data.get('corrections', {})
        if corrections:
            state['applicant_data'].update(corrections)
            state['hitl_data_corrected'] = True
            state['hitl_corrections'] = corrections
        
        # Clear HITL checkpoint
        state['hitl_checkpoint'] = False
        
        logger.info(f"HITL approved for application: {app_id}")
        
        return jsonify({
            'message': 'HITL approved, workflow continuing',
            'corrections_applied': len(corrections)
        }), 200
        
    except Exception as e:
        logger.error(f"Approve HITL error: {e}")
        return jsonify({'error': 'Failed to approve HITL'}), 500
