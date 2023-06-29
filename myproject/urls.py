from django.urls import path
from emailapp.views import email_list

urlpatterns = [
    path('emails/', email_list, name='email_list'),
]
