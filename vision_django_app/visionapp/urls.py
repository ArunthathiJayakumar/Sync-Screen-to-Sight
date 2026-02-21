from django.urls import path
from . import views
from django.shortcuts import render
urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup_view, name='signup'),
    path('signin/', views.signin_view, name='signin'),
    path("logout/",   views.logout_view,   name="logout"),
    path('profile/', views.profile_view, name='profile'),
    path('home', views.home, name='home'),
    path('start_test_page/', views.start_test_page, name='start_test_page'),
    path('start_test', views.start_test, name='start_test'),
    path('check_answer', views.check_answer, name='check_answer'),
    path('final_result', views.final_result, name='final_result'),
    path('process_document/', views.process_document, name='process_document'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('view_file/', views.view_file, name='view_file'),
    path('set_brightness_from_voice/', views.set_brightness_from_voice, name='set_brightness_from_voice'),
    path('export_results/', views.export_results, name='export_results'),
]
