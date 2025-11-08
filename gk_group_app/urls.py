from django.urls import path
from . import views

app_name = 'gk_group_app'

urlpatterns = [
    # Main pages
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('gk-textiles/', views.gk_textiles, name='gk_textiles'),
    path('gk-steels/', views.gk_steels, name='gk_steels'),
    path('contact/', views.contact, name='contact'),

    # Legacy URL patterns (for backward compatibility)
    path('textile/', views.gk_textiles, name='textile_legacy'),
    path('construction/', views.gk_steels, name='construction_legacy'),
]