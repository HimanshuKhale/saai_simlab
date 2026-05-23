from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('labs/<slug:simulation_type_slug>/', views.scenario_list, name='scenario_list'),
    path(
        'labs/<slug:simulation_type_slug>/<slug:scenario_slug>/',
        views.scenario_detail,
        name='scenario_detail',
    ),
    path('scenarios/<int:scenario_id>/start/', views.start_session, name='start_session'),
    path('sessions/<int:session_id>/', views.session_detail, name='session_detail'),
]
