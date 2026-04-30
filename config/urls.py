from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import include, path
from core import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/signup/", core_views.signup, name="signup"),
    path("", include("core.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
