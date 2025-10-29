from django.urls import path
from . import views

app_name = "accounts"  # <-- add this

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("password/change/", views.password_change_ajax, name="password_change_ajax"),
]
