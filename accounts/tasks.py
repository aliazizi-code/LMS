from core.celery import app
from celery import shared_task
from accounts.models import User
from datetime import timedelta
from django.utils import timezone


@app.task
def send_otp_to_phone_tasks(otp):
    print(f'Your OTP is: {otp}')


@app.task
def send_email_tasks(content):
    print(f'Your Token is: http://localhost:8000/auth/email/change/verify/{content}/')


@shared_task
def delete_unlogged_in_users(hours=24):
    # Calculate the date threshold
    hours_ago = timezone.now() - timedelta(hours=hours)

    # Filter users created before the threshold and who haven't logged in
    users_to_delete = User.objects.filter(
        created_at__lt=hours_ago,
        last_login__is_null=True,
        is_superuser=False,
        is_admin=False,
    )

    # Check if there are users to delete
    if not users_to_delete.exists():
        return "No users to delete."

    # Store info of users to be deleted
    deleted_users_info = list(users_to_delete.values('id', 'phone', 'email', 'created_at'))

    # Delete users and get the count
    delete_count = users_to_delete.count()
    users_to_delete.delete()

    # Return count and deleted users' info
    return {
        'delete_count': delete_count,
        'deleted_users': deleted_users_info
    }

