from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('complaint/', views.complaint_view, name='complaint'),
    path('fee/', views.fee_view, name='fee'),
    path('room/', views.room_allocation, name='room'),
    path('status/', views.status_view, name='status'),
    path('profile/', views.profile_view, name='profile'),
]