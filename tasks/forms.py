from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone

from .models import Category, Note, Priority, SubTask, Task


def _widget_classes(widget):
    base = "form-control"
    if isinstance(widget, forms.Select):
        return f"{base} form-select"
    return base


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = _widget_classes(field.widget)
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault("rows", 5)


class FrontendAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username",
                "autofocus": True,
            }
        )
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
            }
        ),
    )


class TaskForm(StyledModelForm):
    deadline = forms.DateTimeField(
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={
                "class": "form-control",
                "type": "datetime-local",
            },
        ),
    )

    class Meta:
        model = Task
        fields = ["title", "description", "status", "category", "priority", "deadline"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.deadline:
            deadline = self.instance.deadline
            if timezone.is_aware(deadline):
                deadline = timezone.localtime(deadline)
            self.initial["deadline"] = deadline.strftime("%Y-%m-%dT%H:%M")


class SubTaskForm(StyledModelForm):
    class Meta:
        model = SubTask
        fields = ["task", "title", "status"]


class CategoryForm(StyledModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class PriorityForm(StyledModelForm):
    class Meta:
        model = Priority
        fields = ["name"]


class NoteForm(StyledModelForm):
    class Meta:
        model = Note
        fields = ["task", "content"]
