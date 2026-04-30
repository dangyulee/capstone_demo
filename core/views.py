import calendar
import html as html_module
from datetime import date

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProjectTopicForm, ScheduleEventForm
from .models import FileReviewItem, Project, ProjectFile, ProjectReference, ScheduleEvent, Team, TeamMember, TeamReview, TeamReviewItem


def _get_project_for_user(user):
    """유저의 첫 번째 팀에 연결된 프로젝트를 반환. 없으면 생성."""
    if user and user.is_authenticated:
        team = user.teams.first()
        if team:
            project = team.projects.first()
            if not project:
                project = Project.objects.create(team=team, title='', description='')
            return project
    # 팀이 없는 경우 임시 개인 프로젝트
    project, _ = Project.objects.get_or_create(id=1, defaults={'title': '', 'description': ''})
    return project


def _base_context(tab='', request=None):
    project = _get_project_for_user(request.user if request else None)
    ctx = {'tab': tab, 'current_project': project}
    if request and request.user.is_authenticated:
        ctx['user_teams'] = request.user.teams.all()
        ctx['current_team'] = request.user.teams.first()
    return ctx


# ── 인증 ─────────────────────────────────────────────────────────
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('project_settings_topic')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


# ── 메인 리다이렉트 ──────────────────────────────────────────────
def index(request):
    return redirect('project_settings_topic')


# ── 자료 검증 탭 ────────────────────────────────────────────────
@login_required
def review(request):
    project = _get_project_for_user(request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'submit_text':
            content = request.POST.get('content', '').strip()
            topic = request.POST.get('topic', '').strip()
            uploaded = request.FILES.get('file')
            ALLOWED = ('.pdf',)
            file_ok = uploaded and uploaded.name.lower().endswith(ALLOWED)
            if content or file_ok:
                name = topic or (uploaded.name if file_ok else '텍스트 입력')
                pf = ProjectFile(
                    project=project,
                    original_name=name,
                    file_size=uploaded.size if file_ok else 0,
                    content=content,
                    topic=topic,
                    status='pending',
                    uploaded_by=request.user,
                )
                if file_ok:
                    pf.file.save(uploaded.name, uploaded)
                else:
                    pf.save()
        elif action == 'verify':
            file_id = request.POST.get('file_id')
            ProjectFile.objects.filter(id=file_id, project=project).update(status='verified')
        elif action == 'reject':
            file_id = request.POST.get('file_id')
            ProjectFile.objects.filter(id=file_id, project=project).update(status='rejected')
        elif action == 'delete_doc':
            file_id = request.POST.get('file_id')
            pf = ProjectFile.objects.filter(id=file_id, project=project).first()
            if pf:
                pf.file.delete(save=False)
                pf.delete()
        elif action == 'submit_review':
            file_id = request.POST.get('file_id')
            vote = request.POST.get('vote')
            comment = request.POST.get('comment', '').strip()
            if file_id and vote:
                pf = ProjectFile.objects.filter(id=file_id, project=project).first()
                if pf:
                    TeamReview.objects.update_or_create(
                        project_file=pf,
                        reviewer=request.user,
                        defaults={'vote': vote, 'comment': comment},
                    )
            return redirect(f'/review/?doc={file_id}')
        elif action == 'submit_team_review':
            file_id = request.POST.get('file_id')
            hl = request.POST.get('highlighted_text', '').strip()
            problem = request.POST.get('problem', '').strip()
            suggestion = request.POST.get('suggestion', '').strip()
            if file_id and hl and problem:
                pf = ProjectFile.objects.filter(id=file_id, project=project).first()
                if pf:
                    TeamReviewItem.objects.create(
                        project_file=pf,
                        reviewer=request.user,
                        highlighted_text=hl,
                        problem=problem,
                        suggestion=suggestion,
                    )
            return redirect(f'/review/?doc={file_id}')
        elif action == 'delete_team_review':
            item_id = request.POST.get('item_id')
            file_id = request.POST.get('file_id')
            TeamReviewItem.objects.filter(id=item_id, reviewer=request.user).delete()
            return redirect(f'/review/?doc={file_id}')
        return redirect('review')

    selected_id = request.GET.get('doc')
    doc_files = project.files.all()
    selected_file = None
    if selected_id:
        selected_file = project.files.filter(id=selected_id).first()

    highlighted_content = None
    team_review_items = []
    reviewer_groups = []
    if selected_file:
        team_review_items = list(selected_file.team_review_items.select_related('reviewer').all())

        # 팀 전체 멤버(본인 제외) 기준으로 reviewer_groups 구성
        team_obj = project.team
        all_members = list(team_obj.members.exclude(id=request.user.id)) if team_obj else []

        votes = {
            v.reviewer.id: v
            for v in selected_file.team_reviews.select_related('reviewer').all()
        }
        items_by_rid = {}
        for i, item in enumerate(team_review_items):
            if item.reviewer == request.user:
                continue
            rid = item.reviewer.id
            items_by_rid.setdefault(rid, []).append({'index': i, 'item': item})

        for member in all_members:
            reviewer_groups.append({
                'reviewer': member,
                'vote': votes.get(member.id),
                'items': items_by_rid.get(member.id, []),
            })
    if selected_file and selected_file.content:
        ai_items = list(selected_file.review_items.all())
        if ai_items or team_review_items:
            escaped = html_module.escape(selected_file.content)
            for i, item in enumerate(ai_items):
                hl = html_module.escape(item.highlighted_text)
                mark = (f'<mark class="review-highlight ai-hl" data-idx="{i}" '
                        f'onclick="focusCard({i})">{hl}</mark>')
                escaped = escaped.replace(hl, mark, 1)
            for i, item in enumerate(team_review_items):
                hl = html_module.escape(item.highlighted_text)
                mark = (f'<mark class="review-highlight team-hl" data-tidx="{i}" '
                        f'onclick="focusTeamCard({i})">{hl}</mark>')
                escaped = escaped.replace(hl, mark, 1)
            highlighted_content = escaped.replace('\n', '<br>')

    other_review_count = sum(len(g['items']) for g in reviewer_groups)
    my_team_review_items = []
    my_review_indices = []
    my_vote = None
    if selected_file:
        my_team_review_items = list(
            selected_file.team_review_items.filter(reviewer=request.user)
        )
        my_review_indices = [
            i for i, item in enumerate(team_review_items)
            if item.reviewer == request.user
        ]
        vote_obj = selected_file.team_reviews.filter(reviewer=request.user).first()
        my_vote = vote_obj.vote if vote_obj else None

    ctx = _base_context('review', request)
    ctx.update({
        'project': project,
        'doc_files': doc_files,
        'selected_file': selected_file,
        'highlighted_content': highlighted_content,
        'team_review_items': team_review_items,
        'reviewer_groups': reviewer_groups,
        'my_team_review_items': my_team_review_items,
        'my_review_indices': my_review_indices,
        'my_vote': my_vote,
        'other_review_count': other_review_count,
    })
    return render(request, 'core/review.html', ctx)


# ── 자료 보관함 탭 ───────────────────────────────────────────────
@login_required
def archive(request):
    project = _get_project_for_user(request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        file_id = request.POST.get('file_id')
        if action == 'verify':
            ProjectFile.objects.filter(id=file_id, project=project).update(status='verified')
        elif action == 'reject':
            ProjectFile.objects.filter(id=file_id, project=project).update(status='rejected')
        elif action == 'delete_doc':
            pf = ProjectFile.objects.filter(id=file_id, project=project).first()
            if pf:
                pf.file.delete(save=False)
                pf.delete()
        return redirect('archive')

    pending_files  = project.files.filter(status='pending')
    verified_files = project.files.filter(status='verified')
    rejected_files = project.files.filter(status='rejected')

    ctx = _base_context('archive', request)
    ctx.update({
        'project': project,
        'pending_files': pending_files,
        'verified_files': verified_files,
        'rejected_files': rejected_files,
    })
    return render(request, 'core/archive.html', ctx)


# ── 내보내기 탭 ─────────────────────────────────────────────────
@login_required
def export(request):
    ctx = _base_context('export', request)
    return render(request, 'core/export.html', ctx)


# ── 팀 관리 ─────────────────────────────────────────────────────
@login_required
def team_list(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_team':
            name = request.POST.get('name', '').strip()
            if name:
                team = Team.objects.create(name=name, join_code=Team.generate_code())
                team.members.add(request.user)
        elif action == 'join_team':
            code = request.POST.get('join_code', '').strip()
            try:
                team = Team.objects.get(join_code=code)
                team.members.add(request.user)
            except Team.DoesNotExist:
                ctx = _base_context('teams', request)
                ctx['all_teams'] = Team.objects.all()
                ctx['error'] = f'입장 코드 {code}에 해당하는 팀이 없습니다.'
                return render(request, 'core/team_list.html', ctx)
        elif action == 'delete_team':
            team_id = request.POST.get('team_id')
            Team.objects.filter(id=team_id).delete()
        return redirect('team_list')

    ctx = _base_context('teams', request)
    ctx['all_teams'] = Team.objects.all()
    return render(request, 'core/team_list.html', ctx)


# ── 프로젝트 설정: 주제 설정 ────────────────────────────────────
@login_required
def project_settings_topic(request):
    project = _get_project_for_user(request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save_team_name':
            name = request.POST.get('team_name', '').strip()
            if name and project.team:
                project.team.name = name
                project.team.save(update_fields=['name'])
            return redirect('project_settings_topic')
        elif action == 'save_topic':
            form = ProjectTopicForm(request.POST, instance=project)
            if form.is_valid():
                form.save()
                return redirect('project_settings_topic')
        elif action == 'upload_file':
            uploaded = request.FILES.get('file')
            if uploaded:
                pr = ProjectReference(
                    project=project,
                    original_name=uploaded.name,
                    file_size=uploaded.size,
                    uploaded_by=request.user,
                )
                pr.file.save(uploaded.name, uploaded)
                pr.save()
            return redirect('project_settings_topic')
    else:
        form = ProjectTopicForm(instance=project)

    ctx = _base_context('settings', request)
    ctx.update({
        'sub_tab': 'topic',
        'project': project,
        'form': form,
        'files': project.references.all(),
    })
    return render(request, 'core/project_settings_topic.html', ctx)


@require_POST
@login_required
def delete_file(request, file_id):
    pr = get_object_or_404(ProjectReference, id=file_id)
    pr.file.delete(save=False)
    pr.delete()
    return redirect('project_settings_topic')


# ── 프로젝트 설정: 역할 분담 ────────────────────────────────────
@login_required
def project_settings_role(request):
    project = _get_project_for_user(request.user)
    team = project.team

    # 팀원 계정과 TeamMember 자동 동기화
    if team:
        for i, user in enumerate(team.members.all()):
            TeamMember.objects.get_or_create(
                project=project, user=user,
                defaults={'name': user.username, 'role': '기타', 'order': i},
            )

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save_roles':
            user_ids = request.POST.getlist('user_id')
            roles = request.POST.getlist('role')
            for uid, role in zip(user_ids, roles):
                TeamMember.objects.filter(project=project, user_id=uid).update(role=role)
        return redirect('project_settings_role')

    ctx = _base_context('settings', request)
    ctx.update({
        'sub_tab': 'role',
        'project': project,
        'members': project.members.select_related('user').order_by('order', 'id'),
        'role_choices': TeamMember.ROLE_CHOICES,
    })
    return render(request, 'core/project_settings_role.html', ctx)


@require_POST
@login_required
def delete_member(request, member_id):
    member = get_object_or_404(TeamMember, id=member_id)
    member.delete()
    return redirect('project_settings_role')


# ── 프로젝트 설정: 스케줄 ───────────────────────────────────────
@login_required
def project_settings_schedule(request):
    project = _get_project_for_user(request.user)

    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_event':
            form = ScheduleEventForm(request.POST)
            if form.is_valid():
                event = form.save(commit=False)
                event.project = project
                event.save()
        elif action == 'delete_event':
            event_id = request.POST.get('event_id')
            ScheduleEvent.objects.filter(id=event_id, project=project).delete()
        return redirect(f'/settings/schedule/?year={year}&month={month}')

    cal = calendar.monthcalendar(year, month)
    events = project.events.filter(date__year=year, date__month=month)
    events_by_day = {}
    for e in events:
        events_by_day.setdefault(e.date.day, []).append(e)

    weeks = []
    for week in cal:
        week_days = []
        for day in week:
            week_days.append({
                'day': day,
                'events': events_by_day.get(day, []) if day != 0 else [],
                'is_today': (day != 0 and date(year, month, day) == date.today()),
                'is_sunday': False,
                'is_saturday': False,
            })
        week_days[0]['is_sunday'] = True
        week_days[6]['is_saturday'] = True
        weeks.append(week_days)

    prev_year, prev_month = (year, month - 1) if month > 1 else (year - 1, 12)
    next_year, next_month = (year, month + 1) if month < 12 else (year + 1, 1)

    ctx = _base_context('settings', request)
    ctx.update({
        'sub_tab': 'schedule',
        'project': project,
        'year': year,
        'month': month,
        'weeks': weeks,
        'form': ScheduleEventForm(),
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'all_events': project.events.all(),
    })
    return render(request, 'core/project_settings_schedule.html', ctx)
