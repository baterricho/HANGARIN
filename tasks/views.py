from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.text import slugify
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from .forms import (
    CategoryForm,
    FrontendAuthenticationForm,
    NoteForm,
    PriorityForm,
    SubTaskForm,
    TaskForm,
)
from .models import Category, Note, Priority, StatusChoices, SubTask, Task
from .social_profiles import resolve_user_avatar_text, resolve_user_display_name

NAVIGATION = (
    {"section": "dashboard", "label": "Dashboard", "icon": "dashboard", "url_name": "tasks:dashboard"},
    {"section": "tasks", "label": "Tasks", "icon": "task_alt", "url_name": "tasks:task-list"},
    {"section": "subtasks", "label": "Sub Tasks", "icon": "account_tree", "url_name": "tasks:subtask-list"},
    {"section": "categories", "label": "Categories", "icon": "category", "url_name": "tasks:category-list"},
    {"section": "priorities", "label": "Priorities", "icon": "flag", "url_name": "tasks:priority-list"},
    {"section": "notes", "label": "Notes", "icon": "sticky_note_2", "url_name": "tasks:note-list"},
)


def format_datetime(value):
    if not value:
        return "No schedule"
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    else:
        value = timezone.localtime(value)
    return value.strftime("%b %d, %Y - %I:%M %p")


def shorten(value, limit=84):
    clean_value = " ".join(value.split())
    if len(clean_value) <= limit:
        return clean_value
    return f"{clean_value[: limit - 3].rstrip()}..."


def percentage(part, whole):
    if not whole:
        return 0
    return round((part / whole) * 100)


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect("tasks:dashboard")
    return redirect("tasks:login")


class FrontendLoginView(LoginView):
    authentication_form = FrontendAuthenticationForm
    redirect_authenticated_user = True
    template_name = "tasks/login.html"

    def get_success_url(self):
        return reverse("tasks:dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "today": timezone.localdate(),
                "google_oauth_enabled": settings.GOOGLE_OAUTH_ENABLED,
                "github_oauth_enabled": settings.GITHUB_OAUTH_ENABLED,
            }
        )
        return context


class FrontendLogoutView(LogoutView):
    next_page = reverse_lazy("tasks:login")


class FrontendContextMixin(LoginRequiredMixin):
    login_url = reverse_lazy("tasks:login")
    page_title = ""
    page_description = ""
    section = ""

    def get_nav_items(self):
        return [
            {
                "label": item["label"],
                "icon": item["icon"],
                "url": reverse(item["url_name"]),
                "active": self.section == item["section"],
            }
            for item in NAVIGATION
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": self.page_title,
                "page_description": self.page_description,
                "nav_items": self.get_nav_items(),
                "today": timezone.localdate(),
                "user_display_name": resolve_user_display_name(self.request.user),
                "user_avatar_text": resolve_user_avatar_text(self.request.user),
            }
        )
        return context


class DashboardView(FrontendContextMixin, TemplateView):
    template_name = "tasks/dashboard.html"
    page_title = "Dashboard"
    page_description = ""
    section = "dashboard"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = Task.objects.select_related("category", "priority")
        total_tasks = tasks.count()
        pending_count = tasks.filter(status=StatusChoices.PENDING).count()
        in_progress_count = tasks.filter(status=StatusChoices.IN_PROGRESS).count()
        completed_count = tasks.filter(status=StatusChoices.COMPLETED).count()

        context.update(
            {
                "status_cards": [
                    {
                        "label": "Total Tasks",
                        "value": total_tasks,
                        "tone": "total",
                        "href": reverse("tasks:task-list"),
                    },
                    {
                        "label": "Pending",
                        "value": pending_count,
                        "tone": "pending",
                        "href": reverse("tasks:task-list"),
                    },
                    {
                        "label": "In Progress",
                        "value": in_progress_count,
                        "tone": "progress",
                        "href": reverse("tasks:task-list"),
                    },
                    {
                        "label": "Completed",
                        "value": completed_count,
                        "tone": "complete",
                        "href": reverse("tasks:task-list"),
                    },
                ],
                "status_breakdown": [
                    {
                        "label": "Pending",
                        "count": pending_count,
                        "percentage": percentage(pending_count, total_tasks),
                        "slug": "pending",
                    },
                    {
                        "label": "In Progress",
                        "count": in_progress_count,
                        "percentage": percentage(in_progress_count, total_tasks),
                        "slug": "in-progress",
                    },
                    {
                        "label": "Completed",
                        "count": completed_count,
                        "percentage": percentage(completed_count, total_tasks),
                        "slug": "completed",
                    },
                ],
                "support_metrics": [
                    {"label": "Subtasks", "value": SubTask.objects.count()},
                    {"label": "Notes", "value": Note.objects.count()},
                    {"label": "Categories", "value": Category.objects.count()},
                    {"label": "Priorities", "value": Priority.objects.count()},
                ],
                "recent_tasks": tasks.order_by("-updated_at")[:6],
                "upcoming_deadlines": tasks.filter(deadline__isnull=False).order_by("deadline")[:5],
                "category_highlights": Category.objects.annotate(task_total=Count("tasks"))
                .order_by("-task_total", "name")[:5],
            }
        )
        return context


class SearchableListView(FrontendContextMixin, ListView):
    template_name = "tasks/entity_list.html"
    paginate_by = 8
    search_fields = ()
    search_placeholder = "Search ..."
    create_url_name = ""
    create_label = "Add Item"
    table_columns = ()
    empty_message = "Nothing has been added yet."
    select_related_fields = ()

    def get_query(self):
        return self.request.GET.get("q", "").strip()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.select_related_fields:
            queryset = queryset.select_related(*self.select_related_fields)
        query = self.get_query()
        if query and self.search_fields:
            filters = Q()
            for field in self.search_fields:
                filters |= Q(**{f"{field}__icontains": query})
            queryset = queryset.filter(filters)
        return queryset

    def get_table_rows(self, object_list):
        return []

    def get_summary_pills(self, queryset):
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "query": self.get_query(),
                "search_placeholder": self.search_placeholder,
                "create_url": reverse(self.create_url_name),
                "create_label": self.create_label,
                "table_columns": self.table_columns,
                "table_rows": self.get_table_rows(context["object_list"]),
                "empty_message": self.empty_message,
                "summary_pills": self.get_summary_pills(self.get_queryset()),
            }
        )
        return context


class SuccessMessageMixin:
    success_message = ""

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.success_message:
            messages.success(self.request, self.success_message)
        return response


class FrontendModelFormMixin(FrontendContextMixin):
    template_name = "tasks/entity_form.html"
    success_url_name = ""
    submit_label = "Save"

    def get_success_url(self):
        return reverse(self.success_url_name)

    def get_cancel_url(self):
        return reverse(self.success_url_name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "form_title": self.page_title,
                "form_description": self.page_description,
                "submit_label": self.submit_label,
                "cancel_url": self.get_cancel_url(),
            }
        )
        return context


class TaskListView(SearchableListView):
    model = Task
    page_title = "Tasks"
    page_description = ""
    section = "tasks"
    search_fields = ("title", "description", "category__name", "priority__name", "status")
    search_placeholder = "Search title, description, category, priority, or status"
    create_url_name = "tasks:task-create"
    create_label = "Add Task"
    table_columns = ("Title", "Status", "Category", "Priority", "Deadline", "Updated")
    empty_message = "No tasks found."
    select_related_fields = ("category", "priority")

    def get_table_rows(self, object_list):
        return [
            {
                "cells": [
                    {"value": task.title},
                    {"value": task.status, "kind": "status", "slug": slugify(task.status)},
                    {"value": task.category.name if task.category else "Unassigned"},
                    {"value": task.priority.name if task.priority else "Unassigned"},
                    {"value": format_datetime(task.deadline) if task.deadline else "No deadline"},
                    {"value": format_datetime(task.updated_at)},
                ],
                "action_url": reverse("tasks:task-update", args=[task.pk]),
                "action_label": "Edit",
            }
            for task in object_list
        ]

    def get_summary_pills(self, queryset):
        return [
            {"label": "Tasks", "value": queryset.count()},
            {"label": "Pending", "value": queryset.filter(status=StatusChoices.PENDING).count()},
            {
                "label": "In Progress",
                "value": queryset.filter(status=StatusChoices.IN_PROGRESS).count(),
            },
            {"label": "Completed", "value": queryset.filter(status=StatusChoices.COMPLETED).count()},
        ]


class TaskCreateView(SuccessMessageMixin, FrontendModelFormMixin, CreateView):
    model = Task
    form_class = TaskForm
    page_title = "Create Task"
    page_description = (
        "Add a new task from the frontend. The record is saved to the same database "
        "used by Django admin."
    )
    section = "tasks"
    success_url_name = "tasks:task-list"
    submit_label = "Create Task"
    success_message = "Task created successfully."


class TaskUpdateView(SuccessMessageMixin, FrontendModelFormMixin, UpdateView):
    model = Task
    form_class = TaskForm
    page_title = "Edit Task"
    page_description = "Update task details without leaving the dashboard frontend."
    section = "tasks"
    success_url_name = "tasks:task-list"
    submit_label = "Save Changes"
    success_message = "Task updated successfully."


class SubTaskListView(SearchableListView):
    model = SubTask
    page_title = "Sub Tasks"
    page_description = ""
    section = "subtasks"
    search_fields = ("title", "status", "task__title")
    search_placeholder = "Search sub task title, status, or parent task"
    create_url_name = "tasks:subtask-create"
    create_label = "Add Sub Task"
    table_columns = ("Title", "Parent Task", "Status", "Updated")
    empty_message = "No sub tasks found."
    select_related_fields = ("task",)

    def get_table_rows(self, object_list):
        return [
            {
                "cells": [
                    {"value": subtask.title},
                    {"value": subtask.task.title},
                    {"value": subtask.status, "kind": "status", "slug": slugify(subtask.status)},
                    {"value": format_datetime(subtask.updated_at)},
                ],
                "action_url": reverse("tasks:subtask-update", args=[subtask.pk]),
                "action_label": "Edit",
            }
            for subtask in object_list
        ]

    def get_summary_pills(self, queryset):
        return [
            {"label": "Sub Tasks", "value": queryset.count()},
            {"label": "Pending", "value": queryset.filter(status=StatusChoices.PENDING).count()},
            {
                "label": "In Progress",
                "value": queryset.filter(status=StatusChoices.IN_PROGRESS).count(),
            },
            {"label": "Completed", "value": queryset.filter(status=StatusChoices.COMPLETED).count()},
        ]


class SubTaskCreateView(SuccessMessageMixin, FrontendModelFormMixin, CreateView):
    model = SubTask
    form_class = SubTaskForm
    page_title = "Create Sub Task"
    page_description = "Add a task item underneath an existing task."
    section = "subtasks"
    success_url_name = "tasks:subtask-list"
    submit_label = "Create Sub Task"
    success_message = "Sub task created successfully."


class SubTaskUpdateView(SuccessMessageMixin, FrontendModelFormMixin, UpdateView):
    model = SubTask
    form_class = SubTaskForm
    page_title = "Edit Sub Task"
    page_description = "Refine progress on a child task directly from the frontend."
    section = "subtasks"
    success_url_name = "tasks:subtask-list"
    submit_label = "Save Changes"
    success_message = "Sub task updated successfully."


class CategoryListView(SearchableListView):
    model = Category
    page_title = "Categories"
    page_description = ""
    section = "categories"
    search_fields = ("name",)
    search_placeholder = "Search category name"
    create_url_name = "tasks:category-create"
    create_label = "Add Category"
    table_columns = ("Name", "Tasks Linked", "Updated")
    empty_message = "No categories found."

    def get_queryset(self):
        return super().get_queryset().annotate(task_total=Count("tasks"))

    def get_table_rows(self, object_list):
        return [
            {
                "cells": [
                    {"value": category.name},
                    {"value": category.task_total},
                    {"value": format_datetime(category.updated_at)},
                ],
                "action_url": reverse("tasks:category-update", args=[category.pk]),
                "action_label": "Edit",
            }
            for category in object_list
        ]

    def get_summary_pills(self, queryset):
        return [
            {"label": "Categories", "value": queryset.count()},
            {"label": "Assigned Tasks", "value": Task.objects.filter(category__isnull=False).count()},
        ]


class CategoryCreateView(SuccessMessageMixin, FrontendModelFormMixin, CreateView):
    model = Category
    form_class = CategoryForm
    page_title = "Create Category"
    page_description = "Create a reusable category for task organization."
    section = "categories"
    success_url_name = "tasks:category-list"
    submit_label = "Create Category"
    success_message = "Category created successfully."


class CategoryUpdateView(SuccessMessageMixin, FrontendModelFormMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    page_title = "Edit Category"
    page_description = "Rename or adjust a category used by existing tasks."
    section = "categories"
    success_url_name = "tasks:category-list"
    submit_label = "Save Changes"
    success_message = "Category updated successfully."


class PriorityListView(SearchableListView):
    model = Priority
    page_title = "Priorities"
    page_description = ""
    section = "priorities"
    search_fields = ("name",)
    search_placeholder = "Search priority name"
    create_url_name = "tasks:priority-create"
    create_label = "Add Priority"
    table_columns = ("Name", "Tasks Linked", "Updated")
    empty_message = "No priorities found."

    def get_queryset(self):
        return super().get_queryset().annotate(task_total=Count("tasks"))

    def get_table_rows(self, object_list):
        return [
            {
                "cells": [
                    {"value": priority.name},
                    {"value": priority.task_total},
                    {"value": format_datetime(priority.updated_at)},
                ],
                "action_url": reverse("tasks:priority-update", args=[priority.pk]),
                "action_label": "Edit",
            }
            for priority in object_list
        ]

    def get_summary_pills(self, queryset):
        return [
            {"label": "Priorities", "value": queryset.count()},
            {"label": "Tagged Tasks", "value": Task.objects.filter(priority__isnull=False).count()},
        ]


class PriorityCreateView(SuccessMessageMixin, FrontendModelFormMixin, CreateView):
    model = Priority
    form_class = PriorityForm
    page_title = "Create Priority"
    page_description = "Add another priority band for task planning."
    section = "priorities"
    success_url_name = "tasks:priority-list"
    submit_label = "Create Priority"
    success_message = "Priority created successfully."


class PriorityUpdateView(SuccessMessageMixin, FrontendModelFormMixin, UpdateView):
    model = Priority
    form_class = PriorityForm
    page_title = "Edit Priority"
    page_description = "Refine how urgency is labeled in the dashboard."
    section = "priorities"
    success_url_name = "tasks:priority-list"
    submit_label = "Save Changes"
    success_message = "Priority updated successfully."


class NoteListView(SearchableListView):
    model = Note
    page_title = "Notes"
    page_description = ""
    section = "notes"
    search_fields = ("content", "task__title")
    search_placeholder = "Search note content or task title"
    create_url_name = "tasks:note-create"
    create_label = "Add Note"
    table_columns = ("Task", "Note", "Created", "Updated")
    empty_message = "No notes found."
    select_related_fields = ("task",)

    def get_table_rows(self, object_list):
        return [
            {
                "cells": [
                    {"value": note.task.title},
                    {"value": shorten(note.content)},
                    {"value": format_datetime(note.created_at)},
                    {"value": format_datetime(note.updated_at)},
                ],
                "action_url": reverse("tasks:note-update", args=[note.pk]),
                "action_label": "Edit",
            }
            for note in object_list
        ]

    def get_summary_pills(self, queryset):
        return [
            {"label": "Notes", "value": queryset.count()},
            {"label": "Tasks With Notes", "value": queryset.values("task_id").distinct().count()},
        ]


class NoteCreateView(SuccessMessageMixin, FrontendModelFormMixin, CreateView):
    model = Note
    form_class = NoteForm
    page_title = "Create Note"
    page_description = "Attach reference information to a task."
    section = "notes"
    success_url_name = "tasks:note-list"
    submit_label = "Create Note"
    success_message = "Note created successfully."


class NoteUpdateView(SuccessMessageMixin, FrontendModelFormMixin, UpdateView):
    model = Note
    form_class = NoteForm
    page_title = "Edit Note"
    page_description = "Update the note content stored with a task."
    section = "notes"
    success_url_name = "tasks:note-list"
    submit_label = "Save Changes"
    success_message = "Note updated successfully."
