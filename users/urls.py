from django.urls import path, include
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register' ),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_views, name='profile'),

    path('account_details/', views.account_details, name='account_details'),
    path('edit_account_details/', views.edit_account_details, name='edit_account_details'),
    path('update_account_details/', views.update_account_details, name='update_account_details'),

    path('password_reset/', views.password_reset_request, name='password_reset_request'),
    # Юідб і токен який ми повинні були передати в посиланні
    path('password_reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
]

