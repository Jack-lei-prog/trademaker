"""Blueprints 包"""
from .auth_bp import auth_bp
from .chat_bp import chat_bp
from .email_bp import email_bp
from .inquiry_bp import inquiry_bp
from .evaluate_bp import evaluate_bp
from .contact_bp import contact_bp
from .dashboard_bp import dashboard_bp
from .doll_bp import doll_bp

__all__ = ["auth_bp", "chat_bp", "email_bp", "inquiry_bp", "evaluate_bp",
           "contact_bp", "dashboard_bp", "doll_bp"]
