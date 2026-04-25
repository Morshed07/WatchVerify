import firebase_admin
from firebase_admin import credentials, auth
from django.conf import settings


def verify_firebase_token(id_token):
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_FILE)
        firebase_admin.initialize_app(cred)

    return auth.verify_id_token(id_token)
