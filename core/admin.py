from django.contrib import admin
from .models import Project, ProjectFile, ProjectReference, TeamMember, ScheduleEvent

admin.site.register(Project)
admin.site.register(ProjectFile)
admin.site.register(ProjectReference)
admin.site.register(TeamMember)
admin.site.register(ScheduleEvent)
