from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("tasks/", views.task_list_view, name="task_list"),
    path("record/",views.record_view,name="record"),
    path("history/",views.history_view,name="history"),
    path("tasks/<int:task_id>/complete/",views.toggle_task,name="toggle_task"),
    path("tasks/<int:task_id>/dalete/",views.delete_task,name="delete_task"),
    
]