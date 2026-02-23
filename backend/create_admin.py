
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
username = 'admin'
email = 'admin@hydrasnipe.it'
password = 'HydraAdmin2026!'

try:
    if User.objects.filter(username=username).exists():
        print(f"User {username} exists. Resetting password...")
        user = User.objects.get(username=username)
        user.set_password(password)
        user.save()
        print("Password reset successfully.")
    else:
        print(f"Creating user {username}...")
        User.objects.create_superuser(username, email, password)
        print("Superuser created successfully.")
except Exception as e:
    print(f"Error: {e}")
