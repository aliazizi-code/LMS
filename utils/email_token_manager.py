from django.utils.crypto import get_random_string

class EmailTokenManager:

    @staticmethod
    def generate_unique_token(length=72):
        from accounts.models import User
        while True:
            token = get_random_string(length)
            if not User.objects.filter(email_verify_token=token).exists():
                return token
    
    @staticmethod
    def assign_email_token_to_user(user):
        token = EmailTokenManager.generate_unique_token()
        user.email_verify_token = token
        user.save()
    
    @staticmethod
    def is_email_token_valid(user ,token):
        from accounts.models import User
        is_valid = User.objects.filter(id=user.id, email_verify_token=token).exists()
        if is_valid:
            EmailTokenManager.assign_email_token_to_user(user)
        return is_valid
