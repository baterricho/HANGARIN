from django.urls import path

from . import views

app_name = "tasks"

urlpatterns = [
    path("", views.home_redirect, name="home"),
    path("login/", views.FrontendLoginView.as_view(), name="login"),
    path("logout/", views.FrontendLogoutView.as_view(), name="logout"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("tasks/", views.TaskListView.as_view(), name="task-list"),
    path("tasks/new/", views.TaskCreateView.as_view(), name="task-create"),
    path("tasks/<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task-update"),
    path("subtasks/", views.SubTaskListView.as_view(), name="subtask-list"),
    path("subtasks/new/", views.SubTaskCreateView.as_view(), name="subtask-create"),
    path("subtasks/<int:pk>/edit/", views.SubTaskUpdateView.as_view(), name="subtask-update"),
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("categories/new/", views.CategoryCreateView.as_view(), name="category-create"),
    path("categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category-update"),
    path("priorities/", views.PriorityListView.as_view(), name="priority-list"),
    path("priorities/new/", views.PriorityCreateView.as_view(), name="priority-create"),
    path("priorities/<int:pk>/edit/", views.PriorityUpdateView.as_view(), name="priority-update"),
    path("notes/", views.NoteListView.as_view(), name="note-list"),
    path("notes/new/", views.NoteCreateView.as_view(), name="note-create"),
    path("notes/<int:pk>/edit/", views.NoteUpdateView.as_view(), name="note-update"),
]
