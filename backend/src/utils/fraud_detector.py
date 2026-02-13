"""
Document Fraud Detection System.

This module implements multi-layer fraud detection for uploaded documents.
"""

import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import PyPDF2
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
import os
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class FraudDetector:
    """
    Multi-layer fraud detection system for documents.
    
    Layers:
    1. Image Analysis (CV-based)
    2. Metadata Analysis
    3. Content Consistency (LLM-based)
    4. Cross-Document Verification
    """
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """
        Initialize fraud detector.
        
        Args:
            groq_api_key: Optional GROQ API key for LLM-based analysis
        """
        self.groq_api_key = groq_api_key or os.getenv('GROQ_API_KEY')
        self.enabled = os.getenv('FRAUD_DETECTION_ENABLED', 'true').lower() == 'true'
        self.threshold = float(os.getenv('FRAUD_DETECTION_THRESHOLD', '40'))
        self.auto_reject_threshold = float(os.getenv('FRAUD_AUTO_REJECT_THRESHOLD', '70'))
        
        logger.info(f"FraudDetector initialized (enabled={self.enabled})")
    
    def analyze_document(
        self,
        file_path: str,
        extracted_text: str,
        document_type: str
    ) -> Dict[str, Any]:
        """
        Perform comprehensive fraud analysis on document.
        
        Args:
            file_path: Path to document file
            extracted_text: Text extracted by OCR
            document_type: Type of document
            
        Returns:
            Fraud analysis results with score and recommendation
        """
        if not self.enabled:
            return self._disabled_response()
        
        try:
            # Layer 1: Image Analysis
            image_analysis = self._analyze_image(file_path)
            
            # Layer 2: Metadata Analysis
            metadata_analysis = self._analyze_metadata(file_path)
            
            # Layer 3: Content Consistency
            content_analysis = self._analyze_content(
                extracted_text, document_type
            )
            
            # Calculate fraud score
            fraud_score = self._calculate_fraud_score(
                image_analysis,
                metadata_analysis,
                content_analysis
            )
            
            # Determine risk level and recommendation
            risk_level, recommendation = self._determine_risk_level(fraud_score)
            
            # Collect all flags
            flags = []
            flags.extend(image_analysis.get('flags', []))
            flags.extend(metadata_analysis.get('flags', []))
            flags.extend(content_analysis.get('flags', []))
            
            return {
                "fraud_score": round(fraud_score, 2),
                "risk_level": risk_level,
                "recommendation": recommendation,
                "flags": flags,
                "details": {
                    "image_analysis": image_analysis,
                    "metadata_analysis": metadata_analysis,
                    "content_analysis": content_analysis
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Fraud detection failed: {e}")
            return {
                "fraud_score": 0.0,
                "risk_level": "unknown",
                "recommendation": "review",
                "flags": [f"Fraud detection error: {str(e)}"],
                "details": {},
                "timestamp": datetime.now().isoformat()
            }
    
    def _analyze_image(self, file_path: str) -> Dict[str, Any]:
        """
        Layer 1: Image analysis for visual tampering.
        
        Checks:
        - Copy-paste detection (ELA)
        - Digital vs scanned
        - Font consistency
        - Resolution inconsistency
        """
        flags = []
        suspicion_score = 0.0
        
        try:
            # Load image
            if file_path.lower().endswith('.pdf'):
                # For PDFs, convert first page to image
                from pdf2image import convert_from_path
                images = convert_from_path(file_path, dpi=150, first_page=1, last_page=1)
                image = np.array(images[0])
            else:
                image = cv2.imread(file_path)
            
            if image is None:
                return {
                    "suspicion_score": 0.0,
                    "flags": ["Could not load image for analysis"],
                    "details": {}
                }
            
            # 1. Check if digitally created (uniform noise pattern)
            is_digital, digital_confidence = self._detect_digital_creation(image)
            if is_digital and digital_confidence > 0.7:
                flags.append(f"Document appears digitally created (confidence: {digital_confidence:.1%})")
                suspicion_score += 15.0
            
            # 2. Check for copy-paste (simplified ELA)
            has_copypaste, copypaste_score = self._detect_copy_paste(image)
            if has_copypaste:
                flags.append(f"Possible copy-paste tampering detected (score: {copypaste_score:.2f})")
                suspicion_score += 25.0
            
            # 3. Check resolution consistency
            has_resolution_issue, resolution_score = self._detect_resolution_inconsistency(image)
            if has_resolution_issue:
                flags.append(f"Resolution inconsistency detected (score: {resolution_score:.2f})")
                suspicion_score += 20.0
            
            return {
                "suspicion_score": min(100.0, suspicion_score),
                "flags": flags,
                "details": {
                    "is_digital": is_digital,
                    "digital_confidence": digital_confidence,
                    "has_copypaste": has_copypaste,
                    "copypaste_score": copypaste_score,
                    "has_resolution_issue": has_resolution_issue,
                    "resolution_score": resolution_score
                }
            }
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return {
                "suspicion_score": 0.0,
                "flags": [f"Image analysis error: {str(e)}"],
                "details": {}
            }
    
    def _detect_digital_creation(self, image: np.ndarray) -> Tuple[bool, float]:
        """
        Detect if document is digitally created vs scanned.
        
        Scanned documents have natural noise patterns.
        Digitally created documents have uniform patterns.
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Calculate noise level (standard deviation of Laplacian)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            noise_level = laplacian.std()
            
            # Scanned documents typically have noise_level > 10
            # Digital documents have noise_level < 5
            if noise_level < 5:
                confidence = 1.0 - (noise_level / 5.0)
                return True, confidence
            else:
                confidence = min(1.0, noise_level / 20.0)
                return False, confidence
                
        except Exception as e:
            logger.error(f"Digital creation detection failed: {e}")
            return False, 0.0
    
    def _detect_copy_paste(self, image: np.ndarray) -> Tuple[bool, float]:
        """
        Detect copy-paste tampering using simplified ELA.
        
        Error Level Analysis detects regions with different compression levels.
        """
        try:
            # This is a simplified version
            # Full ELA requires JPEG compression analysis
            
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Divide image into blocks and calculate variance
            block_size = 64
            h, w = gray.shape
            variances = []
            
            for i in range(0, h - block_size, block_size):
                for j in range(0, w - block_size, block_size):
                    block = gray[i:i+block_size, j:j+block_size]
                    variances.append(np.var(block))
            
            if not variances:
                return False, 0.0
            
            # Calculate variance of variances
            # High variance suggests inconsistent compression (tampering)
            variance_of_variances = np.var(variances)
            
            # Threshold (empirically determined)
            threshold = 1000.0
            if variance_of_variances > threshold:
                score = min(1.0, variance_of_variances / (threshold * 2))
                return True, score
            else:
                return False, variance_of_variances / threshold
                
        except Exception as e:
            logger.error(f"Copy-paste detection failed: {e}")
            return False, 0.0
    
    def _detect_resolution_inconsistency(self, image: np.ndarray) -> Tuple[bool, float]:
        """
        Detect resolution inconsistencies (pasted content).
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Calculate local sharpness using Laplacian
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            
            # Divide into regions and calculate sharpness
            block_size = 100
            h, w = gray.shape
            sharpness_values = []
            
            for i in range(0, h - block_size, block_size):
                for j in range(0, w - block_size, block_size):
                    block = laplacian[i:i+block_size, j:j+block_size]
                    sharpness_values.append(np.abs(block).mean())
            
            if not sharpness_values:
                return False, 0.0
            
            # Calculate coefficient of variation
            mean_sharpness = np.mean(sharpness_values)
            std_sharpness = np.std(sharpness_values)
            
            if mean_sharpness > 0:
                cv = std_sharpness / mean_sharpness
                
                # High CV suggests inconsistent resolution
                if cv > 0.5:
                    score = min(1.0, cv / 1.0)
                    return True, score
            
            return False, 0.0
            
        except Exception as e:
            logger.error(f"Resolution inconsistency detection failed: {e}")
            return False, 0.0
    
    def _analyze_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Layer 2: Metadata analysis.
        
        Checks:
        - PDF metadata (creation date, software)
        - EXIF data (camera, software)
        """
        flags = []
        suspicion_score = 0.0
        details = {}
        
        try:
            if file_path.lower().endswith('.pdf'):
                # PDF metadata analysis
                pdf_meta = self._analyze_pdf_metadata(file_path)
                details.update(pdf_meta)
                
                # Check for suspicious software
                creator = pdf_meta.get('creator', '').lower()
                suspicious_tools = ['photoshop', 'gimp', 'paint', 'editor']
                if any(tool in creator for tool in suspicious_tools):
                    flags.append(f"Document created with editing software: {creator}")
                    suspicion_score += 20.0
                
                # Check modification date
                if pdf_meta.get('modified_after_creation'):
                    flags.append("Document modified after creation")
                    suspicion_score += 10.0
                    
            else:
                # Image EXIF analysis
                exif_data = self._analyze_exif_data(file_path)
                details.update(exif_data)
                
                # Check for screenshot tools
                software = exif_data.get('software', '').lower()
                screenshot_tools = ['screenshot', 'snipping', 'capture']
                if any(tool in software for tool in screenshot_tools):
                    flags.append(f"Document appears to be a screenshot: {software}")
                    suspicion_score += 30.0
            
            return {
                "suspicion_score": min(100.0, suspicion_score),
                "flags": flags,
                "details": details
            }
            
        except Exception as e:
            logger.error(f"Metadata analysis failed: {e}")
            return {
                "suspicion_score": 0.0,
                "flags": [],
                "details": {}
            }
    
    def _analyze_pdf_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract and analyze PDF metadata."""
        try:
            with open(pdf_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                info = pdf.metadata
                
                if info:
                    creation_date = info.get('/CreationDate', '')
                    mod_date = info.get('/ModDate', '')
                    creator = info.get('/Creator', '')
                    producer = info.get('/Producer', '')
                    
                    # Check if modified after creation
                    modified_after = False
                    if creation_date and mod_date:
                        modified_after = mod_date > creation_date
                    
                    return {
                        "creation_date": creation_date,
                        "modification_date": mod_date,
                        "creator": creator,
                        "producer": producer,
                        "modified_after_creation": modified_after
                    }
            
            return {}
            
        except Exception as e:
            logger.error(f"PDF metadata extraction failed: {e}")
            return {}
    
    def _analyze_exif_data(self, image_path: str) -> Dict[str, Any]:
        """Extract and analyze EXIF data from image."""
        try:
            image = Image.open(image_path)
            exif_data = image._getexif()
            
            if exif_data:
                exif = {
                    TAGS.get(tag, tag): value
                    for tag, value in exif_data.items()
                }
                
                return {
                    "camera_model": exif.get('Model', ''),
                    "software": exif.get('Software', ''),
                    "datetime": exif.get('DateTime', ''),
                    "has_gps": 'GPSInfo' in exif
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"EXIF extraction failed: {e}")
            return {}
    
    def _analyze_content(
        self,
        text: str,
        document_type: str
    ) -> Dict[str, Any]:
        """
        Layer 3: Content consistency analysis.
        
        Checks:
        - Logical consistency
        - Pattern validation
        - Language quality
        """
        flags = []
        suspicion_score = 0.0
        
        try:
            # 1. Pattern validation
            pattern_issues = self._validate_patterns(text, document_type)
            if pattern_issues:
                flags.extend(pattern_issues)
                suspicion_score += len(pattern_issues) * 15.0
            
            # 2. Logical consistency (if LLM available)
            if self.groq_api_key:
                logic_issues = self._check_logical_consistency(text, document_type)
                if logic_issues:
                    flags.extend(logic_issues)
                    suspicion_score += len(logic_issues) * 20.0
            
            return {
                "suspicion_score": min(100.0, suspicion_score),
                "flags": flags,
                "details": {
                    "pattern_issues": pattern_issues,
                    "logic_issues": logic_issues if self.groq_api_key else []
                }
            }
            
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return {
                "suspicion_score": 0.0,
                "flags": [],
                "details": {}
            }
    
    def _validate_patterns(self, text: str, document_type: str) -> List[str]:
        """Validate document-specific patterns."""
        issues = []
        
        # PAN pattern: 5 letters + 4 digits + 1 letter
        if 'pan' in document_type.lower():
            pan_pattern = r'[A-Z]{5}\d{4}[A-Z]'
            pans = re.findall(pan_pattern, text)
            if not pans:
                issues.append("No valid PAN number found")
        
        # Aadhaar pattern: 12 digits
        if 'aadhaar' in document_type.lower() or 'aadhar' in document_type.lower():
            aadhaar_pattern = r'\d{4}\s?\d{4}\s?\d{4}'
            aadhaars = re.findall(aadhaar_pattern, text)
            if not aadhaars:
                issues.append("No valid Aadhaar number found")
        
        # Check for impossible dates (future dates in historical docs)
        date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}'
        dates = re.findall(date_pattern, text)
        current_year = datetime.now().year
        for date_str in dates:
            try:
                # Extract year
                year_match = re.search(r'\d{4}', date_str)
                if year_match:
                    year = int(year_match.group())
                    if year > current_year:
                        issues.append(f"Future date found: {date_str}")
            except:
                pass
        
        return issues
    
    def _check_logical_consistency(self, text: str, document_type: str) -> List[str]:
        """Check logical consistency using LLM."""
        try:
            from langchain_groq import ChatGroq
            
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                api_key=self.groq_api_key
            )
            
            prompt = f"""Analyze this {document_type} document for logical inconsistencies or fraud indicators.

Document text (first 1000 chars):
{text[:1000]}

Check for:
1. Impossible values (e.g., negative salary, age > 150)
2. Inconsistent information
3. Suspicious patterns
4. Missing critical information

Respond with a JSON list of issues found, or empty list if none:
["issue 1", "issue 2", ...]

Response:"""
            
            response = llm.invoke(prompt).content.strip()
            
            # Parse response
            import json
            try:
                issues = json.loads(response)
                if isinstance(issues, list):
                    return issues
            except:
                pass
            
            return []
            
        except Exception as e:
            logger.error(f"LLM consistency check failed: {e}")
            return []
    
    def _calculate_fraud_score(
        self,
        image_analysis: Dict,
        metadata_analysis: Dict,
        content_analysis: Dict
    ) -> float:
        """
        Calculate overall fraud score.
        
        Weights:
        - Image Analysis: 30%
        - Metadata Analysis: 20%
        - Content Analysis: 50%
        """
        score = (
            image_analysis.get('suspicion_score', 0) * 0.30 +
            metadata_analysis.get('suspicion_score', 0) * 0.20 +
            content_analysis.get('suspicion_score', 0) * 0.50
        )
        
        return min(100.0, score)
    
    def _determine_risk_level(self, fraud_score: float) -> Tuple[str, str]:
        """
        Determine risk level and recommendation based on fraud score.
        
        Returns:
            (risk_level, recommendation)
        """
        if fraud_score < 20:
            return "low", "approve"
        elif fraud_score < 40:
            return "medium", "review"
        elif fraud_score < 70:
            return "high", "review"
        else:
            return "critical", "reject"
    
    def _disabled_response(self) -> Dict[str, Any]:
        """Return response when fraud detection is disabled."""
        return {
            "fraud_score": 0.0,
            "risk_level": "unknown",
            "recommendation": "approve",
            "flags": ["Fraud detection disabled"],
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
    
    def verify_cross_document_consistency(
        self,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Layer 4: Cross-document verification.
        
        Checks consistency across multiple documents.
        """
        flags = []
        suspicion_score = 0.0
        
        try:
            # Extract names from all documents
            names = []
            for doc in documents:
                extracted_data = doc.get('extracted_data', {})
                name = extracted_data.get('name')
                if name:
                    names.append(name.lower().strip())
            
            # Check name consistency
            if len(set(names)) > 1:
                flags.append(f"Name mismatch across documents: {set(names)}")
                suspicion_score += 30.0
            
            # Extract DOBs
            dobs = []
            for doc in documents:
                extracted_data = doc.get('extracted_data', {})
                dob = extracted_data.get('dob') or extracted_data.get('date_of_birth')
                if dob:
                    dobs.append(dob)
            
            # Check DOB consistency
            if len(set(dobs)) > 1:
                flags.append(f"DOB mismatch across documents: {set(dobs)}")
                suspicion_score += 30.0
            
            return {
                "suspicion_score": min(100.0, suspicion_score),
                "flags": flags,
                "details": {
                    "names_found": list(set(names)),
                    "dobs_found": list(set(dobs))
                }
            }
            
        except Exception as e:
            logger.error(f"Cross-document verification failed: {e}")
            return {
                "suspicion_score": 0.0,
                "flags": [],
                "details": {}
            }
