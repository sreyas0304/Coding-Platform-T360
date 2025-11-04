# problems/urls.py
from django.urls import path
from .views import health_check, ProblemsView


urlpatterns = [
    path("problems",  ProblemsView.as_view(), name="problems"),       # no slash
    path("problems/", ProblemsView.as_view(), name="problems_slash"), # with slash

    path("check",  health_check, name="check"),
    path("check/", health_check, name="check_slash"),
]
