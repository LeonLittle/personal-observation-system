
from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("tasks/", views.task_list_view, name="task_list"),
    path("record/",views.record_view,name="record"),
    path("history/",views.history_view,name="history"),
    path("habits/<int:habit_id>/pause/", views.pause_habit, name="pause_habit"),
    path("habits/<int:habit_id>/resume/", views.resume_habit, name="resume_habit"),
    path("habits/<int:habit_id>/delete/", views.delete_habit, name="delete_habit"),
    path("habits/", views.habits_view, name="habits"),
    
    path("tasks/<int:task_id>/complete/",views.toggle_task,name="toggle_task"),
    path("tasks/<int:task_id>/focus/", views.toggle_home_focus, name="toggle_home_focus"),
    path("tasks/<int:task_id>/delete/",views.delete_task,name="delete_task"),
    
]