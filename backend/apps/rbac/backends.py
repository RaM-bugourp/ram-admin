"""Custom auth backend — authenticates against our User model."""
from apps.rbac.models import User


class UserBackend:
    """Authenticate using username + password_hash."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        try:
            user = User.objects.get(username=username, is_deleted=False)
        except User.DoesNotExist:
            # Match Django ModelBackend's dummy hash work; no custom sleeps.
            User().set_password(password)
            return None
        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return None
