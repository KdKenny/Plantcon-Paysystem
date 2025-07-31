from django.urls import path
from . import views
app_name = 'pages'
urlpatterns = [
    path('', views.index, name='index'),
    path('logout/', views.logout_view, name='logout'),
]