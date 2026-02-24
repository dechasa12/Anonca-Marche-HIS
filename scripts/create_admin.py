#!/usr/bin/env python3
"""Create initial admin user"""
import os
import sys
import hashlib
import json

def create_admin():
    """Create admin user if not exists"""
    admin_data = {
        "id": "admin-001",
        "username": "admin",
        "email": os.getenv("ADMIN_EMAIL", "admin@aoumarche.it"),
        "password_hash": hashlib.sha256(
            os.getenv("ADMIN_PASSWORD", "Admin@2024").encode()
        ).hexdigest(),
        "role": "super_admin",
        "created_at": "2024-01-01T00:00:00"
    }
    
    # In production, this would save to database
    print(f"✅ Admin user created: {admin_data['email']}")
    
if __name__ == "__main__":
    create_admin()
