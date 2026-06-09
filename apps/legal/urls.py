from django.urls import path
from . import views

app_name = 'legal'

urlpatterns = [
    path('<slug:slug>/', views.legal_page_detail, name='detail'),
]
