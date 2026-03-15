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
    path('pwa_camera/', views.pwa_camera_view, name='pwa_camera'),
    path('api/analyze_frame/', views.analyze_frame, name='analyze_frame'),
    
    # AI Exam Preparation URLs
    path('exam-prep/', views.examprep_dashboard, name='examprep_dashboard'),
    path('exam-prep/upload/', views.upload_study_material, name='upload_study_material'),
    path('exam-prep/materials/', views.study_materials_list, name='study_materials_list'),
    path('exam-prep/materials/<int:material_id>/delete/', views.delete_study_material, name='delete_study_material'),
    path('exam-prep/flashcards/', views.view_flashcards, name='view_flashcards'),
    path('exam-prep/flashcards/material/<int:material_id>/', views.view_flashcards, name='view_flashcards_by_material'),
    path('exam-prep/flashcards/create/', views.create_flashcard, name='create_flashcard'),
    path('exam-prep/api/flashcard/mastery/', views.update_flashcard_mastery, name='update_flashcard_mastery'),
    path('exam-prep/quiz/', views.take_quiz, name='take_quiz'),
    path('exam-prep/quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz_by_id'),
    path('exam-prep/quiz/submit/', views.submit_quiz, name='submit_quiz'),
    path('exam-prep/history/', views.quiz_history, name='quiz_history'),
    path('exam-prep/resources/', views.learning_resources, name='learning_resources'),
    path('exam-prep/progress/', views.study_progress, name='study_progress'),
    
    # AI Study Planner URLs
    path('exam-prep/planner/', views.study_planner, name='study_planner'),
    path('exam-prep/planner/create/', views.create_study_plan, name='create_study_plan'),
    path('exam-prep/planner/<int:plan_id>/', views.view_study_plan, name='view_study_plan'),
    path('exam-prep/planner/<int:plan_id>/delete/', views.delete_study_plan, name='delete_study_plan'),
    path('exam-prep/planner/schedule/<int:item_id>/update/', views.update_schedule_item, name='update_schedule_item'),
    
    # Previous Exam Pattern & Smart Revision URLs
    path('exam-prep/previous-exams/', views.previous_exam_questions, name='previous_exam_questions'),
    path('exam-prep/previous-exams/add/', views.add_previous_exam_question, name='add_previous_exam_question'),
    path('exam-prep/pattern-analysis/', views.exam_pattern_analysis, name='exam_pattern_analysis'),
    path('exam-prep/smart-revision/', views.smart_revision_dashboard, name='smart_revision_dashboard'),
    path('exam-prep/smart-revision/add/', views.add_revision_topic, name='add_revision_topic'),
    path('exam-prep/smart-revision/<int:revision_id>/review/', views.review_topic, name='review_topic'),
    
    # AI Doubt Solver URLs
    path('exam-prep/doubt-solver/', views.doubt_solver, name='doubt_solver'),
    path('exam-prep/doubt-solver/chat/', views.doubt_chat, name='doubt_chat_new'),
    path('exam-prep/doubt-solver/chat/<int:session_id>/', views.doubt_chat, name='doubt_chat'),
    path('exam-prep/doubt-solver/<int:session_id>/delete/', views.delete_doubt_session, name='delete_doubt_session'),
    
    # Auto Notes Generator URLs
    path('exam-prep/auto-notes/', views.auto_notes_generator, name='auto_notes_generator'),
    path('exam-prep/auto-notes/upload/', views.upload_notes_file, name='upload_notes_file'),
    path('exam-prep/auto-notes/<int:notes_id>/', views.view_generated_notes, name='view_generated_notes'),
    path('exam-prep/auto-notes/<int:notes_id>/delete/', views.delete_generated_notes, name='delete_generated_notes'),
]
