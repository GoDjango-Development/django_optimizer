from django.urls import path
from django_optimizer.views import get_service_worker_js, verify_reCAPTCHA
urlpatterns = [
    path("service_worker.js", get_service_worker_js, name="service_worker_script"),
    path("captcha/verify/", verify_reCAPTCHA, name="captcha_protect")
]