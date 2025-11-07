# problems/urls.py
from django.urls import path
from .views import health_check, ProblemsView, TestCaseView, SolutionView


urlpatterns = [
    path("problems",  ProblemsView.as_view(), name="problems"),       # no slash
    path("problems/", ProblemsView.as_view(), name="problems_slash"),  # with slash

    path("problems/<slug:slug>/", ProblemsView.as_view(), name="get_problem"),
    path("problems/<slug:slug>/solution/", SolutionView.as_view(), name="view_solution"),
    path("testcases/", TestCaseView.as_view(), name="test-cases"),

    path("check",  health_check, name="check"),
    path("check/", health_check, name="check_slash"),

]
