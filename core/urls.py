from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
    path('', include('bot.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Логин
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # Обновление токена
]  

