from django.urls import path
from .views import ProblemsView

urlpatterns = [
    path("problems", ProblemsView.as_view()),  # POST=add/upsert, GET=list
]