from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None):
        """
        Creates and saves a User with the given phone and password.
        """
        if not phone:
            raise ValueError("Users must have an phone")

        user = self.model(
            phone=phone
        )

        user.is_active = True
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None):
        """
        Creates and saves a superuser with the given phone and password.
        """
        user = self.create_user(
            phone=phone,
            password=password
        )
        user.is_admin = user.is_superuser = user.is_active = user.is_staff = True
        user.save(using=self._db)
        return user