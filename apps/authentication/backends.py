from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to authenticate using their email address.
    """

    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        """
        Authenticate a user based on email address and password.

        Args:
            request: The request object
            username: Username (will be ignored if email is provided)
            password: User's password
            email: User's email address
            **kwargs: Additional keyword arguments

        Returns:
            User instance if authentication is successful, None otherwise
        """
        # If email is provided, use it. Otherwise, try username as email
        email_to_use = email or username

        if email_to_use is None or password is None:
            return None

        try:
            # Try to fetch the user by searching the email field
            user = User.objects.get(email=email_to_use)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            User().set_password(password)
            return None
        else:
            # Check the password and return the user if valid
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

        return None
