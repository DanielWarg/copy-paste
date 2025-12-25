"""Certificate metadata extraction from mTLS headers.

This module extracts user identity (CN) and role (OU) from client certificate
subject passed via proxy headers. Backend is auth-agnostic but uses this for audit logging.

Privacy-safe: Only extracts metadata, never logs full certificates.
"""
import re
from typing import Optional, Tuple

from fastapi import Request


def extract_cert_metadata(request: Request) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract CN (user_id), OU (role), and O (org) from certificate subject.
    
    Certificate subject format: CN=user_id,OU=role,O=CopyPaste
    
    Args:
        request: FastAPI request with X-Client-Cert-Subject header
        
    Returns:
        Tuple of (user_id, role, org) or (None, None, None) if not found
    """
    subject_header = request.headers.get("X-Client-Cert-Subject", "")
    if not subject_header:
        return None, None, None
    
    # Extract CN (user_id)
    cn_match = re.search(r'CN=([^,]+)', subject_header)
    user_id = cn_match.group(1) if cn_match else None
    
    # Extract OU (role)
    ou_match = re.search(r'OU=([^,]+)', subject_header)
    role = ou_match.group(1) if ou_match else None
    
    # Extract O (organization)
    o_match = re.search(r'O=([^,]+)', subject_header)
    org = o_match.group(1) if o_match else None
    
    return user_id, role, org


def get_user_id(request: Request) -> Optional[str]:
    """Get user ID from certificate metadata.
    
    Args:
        request: FastAPI request
        
    Returns:
        User ID (CN) or None if not found
    """
    user_id, _, _ = extract_cert_metadata(request)
    return user_id


def get_user_role(request: Request) -> Optional[str]:
    """Get user role from certificate metadata.
    
    Args:
        request: FastAPI request
        
    Returns:
        User role (OU) or None if not found
    """
    _, role, _ = extract_cert_metadata(request)
    return role


def get_user_org(request: Request) -> Optional[str]:
    """Get user organization from certificate metadata.
    
    Args:
        request: FastAPI request
        
    Returns:
        User organization (O) or None if not found
    """
    _, _, org = extract_cert_metadata(request)
    return org

