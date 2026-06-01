from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("record/",views.record_view,name="record"),
    path("tasks/<int:task_id>/complete/",views.toggle_task,name="toggle_task"),
    path("tasks/<int:task_id>/dalete/",views.delete_task,name="delete_task"),
    
]