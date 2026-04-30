from django import forms
from .models import Project, TeamMember, ScheduleEvent


class ProjectTopicForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '프로젝트 주제를 입력하세요'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': '상세 설명을 입력하세요'}),
        }
        labels = {
            'title': '주제',
            'description': '상세 설명',
        }


class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = ['name', 'role']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input member-name'}),
            'role': forms.Select(attrs={'class': 'form-select member-role'}),
        }


TeamMemberFormSet = forms.modelformset_factory(
    TeamMember,
    form=TeamMemberForm,
    extra=0,
    can_delete=True,
)


class ScheduleEventForm(forms.ModelForm):
    class Meta:
        model = ScheduleEvent
        fields = ['title', 'date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '일정 제목'}),
            'date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }
