from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

# wims/authentication.py
import logging
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class CookieJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        access_token = request.COOKIES.get("access_token")
        
        logger.info(f"🔹 Access Token from cookie: {access_token}")
        print("🔹 Access Token:", access_token)

        if not access_token:
            logger.warning("🚨 No access token found in cookies!")
            print("🚨 No access token found in cookies!")
            return None

        try:
            decoded_token = AccessToken(access_token)
            user_id = decoded_token["user_id"]
            user = User.objects.get(id=user_id)
            logger.info(f"✅ Successfully authenticated user: {user.username}")
            print(f"✅ Successfully authenticated user: {user.username}")
            return (user, None)

        except AccessToken.ExpiredToken:
            logger.error("⏰ Access token has expired")
            raise AuthenticationFailed("Access token has expired")
        except AccessToken.InvalidToken as e:
            logger.error(f"❌ Invalid access token: {str(e)}")
            raise AuthenticationFailed("Invalid access token")
        except User.DoesNotExist:
            logger.error("👤 User not found")
            raise AuthenticationFailed("User not found")
        except Exception as e:
            logger.error(f"⚠️ Authentication error: {str(e)}")
            raise AuthenticationFailed(f"Authentication error: {str(e)}")