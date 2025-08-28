from django.urls import path
from .views import RemoteCallView

urlpatterns = [
    path("remote_call", RemoteCallView.as_view(), name="remote_call"),
]