from lab_system.app.services.base_service import BaseService
from lab_system.app.services.user_service import authenticate
from lab_system.app.utils.errors import AuthenticationError


class AuthService(BaseService):
    def login(self, username: str, password: str):
        user = authenticate(username, password)
        if not user:
            raise AuthenticationError('بيانات الدخول غير صحيحة')
        return user
