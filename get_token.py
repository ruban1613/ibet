#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from rest_framework.authtoken.models import Token
from student_module.models import User

def get_or_create_token():
    user = User.objects.filter(username='test_dailywage').first()
    if not user:
        print("User not found")
        return None

    token, created = Token.objects.get_or_create(user=user)
    print(f"Token for {user.username}: {token.key}")
    return token.key

if __name__ == '__main__':
    get_or_create_token()
