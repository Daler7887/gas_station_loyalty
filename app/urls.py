from django.urls import path, re_path
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView
)

from app.views import (
    main,
    plate_recog
)
from .views.main import DashboardData, UserInfoView
from app.views.bot_users import BotUserListView
from app.views.fuel_sales import FuelSaleListView
from app.views.bonus import get_bonuses_spent

urlpatterns = [
    # login
    path('accounts/login/', LoginView.as_view()),
    path('changepassword/', PasswordChangeView.as_view(
        template_name='registration/change_password.html'), name='editpassword'),
    path('changepassword/done/', PasswordChangeDoneView.as_view(
        template_name='registration/afterchanging.html'), name='password_change_done'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('upload/', plate_recog.PlateRecognitionView.as_view(),
         name='camera-data-upload'),
    # files
    re_path(r'^files/(?P<path>.*)$', main.get_file),
    path('api/analytics/', DashboardData.as_view(), name='dashboard-data'),
    path('api/user-info/', UserInfoView.as_view(), name='user-info'),
    path('api/bot-users/', BotUserListView.as_view(), name='bot-users'),
    path('api/fuel-sales/', FuelSaleListView.as_view(), name='fuel-sales'),
    path('api/bonuses-spent/', get_bonuses_spent, name='get_bonuses_spent'),
]
