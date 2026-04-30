from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.models import (
    FileReviewItem, Project, ProjectFile, ScheduleEvent,
    TeamMember, TeamReview, TeamReviewItem,
)


class Command(BaseCommand):
    help = '퀄리티 더미 데이터 생성'

    def handle(self, *args, **options):
        self.stdout.write('기존 데이터 초기화 중...')
        ProjectFile.objects.all().delete()
        Project.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        # ── 유저 생성 ────────────────────────────────────────────
        self.stdout.write('유저 생성 중...')
        users = []
        user_info = [
            ('minjun',  '이민준', 'PM'),
            ('seoyeon', '김서연', '프론트'),
            ('jiho',    '박지호', '백엔드'),
            ('yuna',    '최유나', 'AI'),
        ]
        for username, name, role in user_info:
            u = User.objects.create_user(username=username, password='test1234')
            u.first_name = name
            u.save()
            users.append((u, name, role))

        minjun, seoyeon, jiho, yuna = [u for u, _, _ in users]

        # ── 프로젝트 생성 ─────────────────────────────────────────
        self.stdout.write('프로젝트 생성 중...')
        project = Project.objects.create(
            name='AI 강의 추천 팀',
            join_code='247813',
            title='AI 기반 대학교 강의 추천 시스템',
            description=(
                '학생의 전공, 관심사, 수강 이력을 분석하여 최적의 강의를 추천하는 AI 시스템. '
                '협업 필터링과 콘텐츠 기반 필터링을 결합한 하이브리드 모델을 활용하며, '
                '실시간 피드백 반영을 통해 추천 정확도를 지속 개선한다.'
            ),
        )
        for u, _, _ in users:
            project.members.add(u)

        # TeamMember 역할 설정
        for i, (u, name, role) in enumerate(users):
            TeamMember.objects.create(
                project=project, user=u, name=name, role=role, order=i
            )

        # ── 일정 ─────────────────────────────────────────────────
        self.stdout.write('일정 생성 중...')
        today = date.today()
        events = [
            ('킥오프 미팅', today - timedelta(days=28)),
            ('요구사항 분석 완료', today - timedelta(days=21)),
            ('중간 발표', today - timedelta(days=7)),
            ('1차 프로토타입 데모', today + timedelta(days=7)),
            ('사용자 테스트', today + timedelta(days=14)),
            ('최종 발표', today + timedelta(days=35)),
        ]
        for title, dt in events:
            ScheduleEvent.objects.create(project=project, title=title, date=dt)

        # ── 자료 1: 딥러닝 논문 분석 (pending, AI+팀원 리뷰 풍부) ──
        self.stdout.write('자료 생성 중...')
        f1 = ProjectFile.objects.create(
            project=project,
            original_name='딥러닝 기반 협업 필터링 논문 분석',
            file_size=0,
            content=(
                '본 논문은 Neural Collaborative Filtering(NCF) 모델을 기반으로 대학교 강의 추천 시스템을 구현한 연구를 분석한다.\n\n'
                '기존 행렬 분해(Matrix Factorization) 방식은 선형 상호작용만 모델링하는 한계가 있다. '
                'NCF는 다층 퍼셉트론을 도입하여 사용자-아이템 간 비선형 관계를 학습하며, '
                '강의 추천 도메인에서 Top-10 정확도 기준 기존 대비 12.4% 성능 향상을 달성했다.\n\n'
                '데이터셋은 국내 A대학교 4년치 수강 신청 로그 32만 건을 활용하였으며, '
                '콜드 스타트 문제 해결을 위해 학과·학년·GPA 정보를 사이드 피처로 추가했다. '
                '실험 결과 Precision@10 0.71, Recall@10 0.63, NDCG@10 0.68을 기록했다.\n\n'
                '한계로는 강의 설명 텍스트 등 콘텐츠 정보를 활용하지 못하며, '
                '수강 취소 이력이 학습 데이터에서 제외되어 있어 실제 선호도와 괴리가 발생할 수 있다.'
            ),
            topic='딥러닝 협업 필터링',
            status='pending',
            uploaded_by=minjun,
        )
        # AI 리뷰
        ai_reviews_f1 = [
            (
                'NCF는 다층 퍼셉트론을 도입하여 사용자-아이템 간 비선형 관계를 학습하며',
                'NCF 모델의 구체적인 레이어 구조(입력 차원, 히든 레이어 수, 활성화 함수)가 명시되지 않아 재현성이 낮습니다.',
                '모델 구조 다이어그램 또는 하이퍼파라미터 테이블을 추가하여 재현 가능성을 높이세요.',
                0,
            ),
            (
                '국내 A대학교 4년치 수강 신청 로그 32만 건을 활용하였으며',
                '단일 학교 데이터만 사용하여 일반화 가능성이 불분명합니다. 데이터 편향 가능성이 있습니다.',
                '타 대학 데이터셋과 교차 검증하거나, 데이터 대표성 한계를 명시적으로 서술하세요.',
                1,
            ),
            (
                '수강 취소 이력이 학습 데이터에서 제외되어 있어',
                '수강 취소를 부정적 피드백 신호로 활용하지 않으면 implicit feedback 학습이 불완전합니다.',
                '취소 이력을 negative sample로 처리하는 BPR(Bayesian Personalized Ranking) 적용을 검토하세요.',
                2,
            ),
        ]
        for hl, prob, sug, order in ai_reviews_f1:
            FileReviewItem.objects.create(
                project_file=f1,
                highlighted_text=hl,
                problem=prob,
                suggestion=sug,
                order=order,
            )
        # 팀원 리뷰 (seoyeon)
        TeamReviewItem.objects.create(
            project_file=f1,
            reviewer=seoyeon,
            highlighted_text='Precision@10 0.71, Recall@10 0.63, NDCG@10 0.68을 기록했다',
            problem='성능 지표가 어떤 베이스라인과 비교한 것인지 기준이 없어 의미 파악이 어렵습니다.',
            suggestion='최소한 ItemKNN, SVD 등 전통적인 추천 모델과의 비교 테이블을 추가해주세요.',
        )
        TeamReviewItem.objects.create(
            project_file=f1,
            reviewer=jiho,
            highlighted_text='콜드 스타트 문제 해결을 위해 학과·학년·GPA 정보를 사이드 피처로 추가했다',
            problem='GPA를 사이드 피처로 사용하는 것은 개인정보 민감도가 높아 실제 시스템 적용 시 법적 문제가 될 수 있습니다.',
            suggestion='GPA 대신 수강 학점 범위(예: 3.0 이상/미만)처럼 범주화된 값을 사용하거나, 개인정보 처리 방침을 별도로 명시하세요.',
        )
        TeamReview.objects.create(project_file=f1, reviewer=seoyeon, vote='hold',
                                  comment='성능 비교 기준이 보완되면 승인 가능합니다.')
        TeamReview.objects.create(project_file=f1, reviewer=jiho, vote='hold',
                                  comment='GPA 사용 관련 법적 검토가 필요합니다.')
        TeamReview.objects.create(project_file=f1, reviewer=yuna, vote='approve',
                                  comment='AI 관점에서 방법론은 적절합니다. 지적 사항 보완 후 최종 승인 예정.')

        # ── 자료 2: 경쟁 서비스 분석 (verified) ───────────────────
        f2 = ProjectFile.objects.create(
            project=project,
            original_name='경쟁 서비스 벤치마킹 보고서',
            file_size=0,
            content=(
                '본 보고서는 국내외 강의 추천 서비스 4종(Coursera, edX, K-MOOC, 에브리타임)을 분석하여 '
                '차별화 전략을 도출한다.\n\n'
                'Coursera는 학습자 행동 데이터 기반 AI 추천을 제공하나, 국내 대학 학점 연계가 부재하다. '
                'edX는 전문자격증 중심으로 학부 교양 추천에는 한계가 있다. '
                'K-MOOC은 국내 대학 강의를 보유하나 추천 알고리즘이 단순 인기도 기반에 그친다. '
                '에브리타임은 강의 평가 데이터가 풍부하나 체계적 추천 기능이 없다.\n\n'
                '결론적으로 국내 대학 학사 시스템 연동 + AI 개인화 추천을 결합한 서비스는 '
                '현재 시장에 존재하지 않으며, 이것이 본 프로젝트의 핵심 차별점이다.'
            ),
            topic='시장 조사',
            status='verified',
            uploaded_by=seoyeon,
        )
        FileReviewItem.objects.create(
            project_file=f2,
            highlighted_text='K-MOOC은 국내 대학 강의를 보유하나 추천 알고리즘이 단순 인기도 기반에 그친다',
            problem='K-MOOC의 추천 방식을 "인기도 기반"으로 단정하는 근거 자료가 부족합니다.',
            suggestion='공식 문서 또는 논문 인용을 통해 K-MOOC 알고리즘 특성을 뒷받침하세요.',
            order=0,
        )
        TeamReview.objects.create(project_file=f2, reviewer=minjun, vote='approve',
                                  comment='차별화 포인트가 명확하게 정리되었습니다.')
        TeamReview.objects.create(project_file=f2, reviewer=jiho, vote='approve',
                                  comment='K-MOOC 관련 근거 자료 추가 요망이나 전체 방향은 동의합니다.')

        # ── 자료 3: 사용자 설문 분석 (pending, 리뷰 진행 중) ──────
        f3 = ProjectFile.objects.create(
            project=project,
            original_name='사용자 설문 결과 분석',
            file_size=0,
            content=(
                '재학생 127명을 대상으로 온라인 설문을 실시하였다 (응답률 63.5%, 유효 응답 82건).\n\n'
                '강의 선택 시 가장 중요하게 고려하는 요소(복수 응답): '
                '교수 평판 78.0%, 과목 내용 73.2%, 학점 취득 난이도 61.0%, 시간표 적합성 54.9%, '
                '취업 연계성 41.5%.\n\n'
                'AI 추천 서비스 사용 의향: 매우 그렇다 31.7%, 그렇다 45.1%, 보통 17.1%, 아니다 6.1%.\n\n'
                '추천 시스템에 제공하고 싶지 않은 정보(민감 정보): GPA 67.1%, 출결 현황 52.4%, '
                '세부 성적 48.8%.'
            ),
            topic='사용자 조사',
            status='pending',
            uploaded_by=yuna,
        )
        FileReviewItem.objects.create(
            project_file=f3,
            highlighted_text='응답률 63.5%, 유효 응답 82건',
            problem='전체 모집단(재학생 수) 대비 표본 크기가 명시되지 않아 대표성 평가가 어렵습니다.',
            suggestion='학과별·학년별 응답자 비율을 층화 표본과 비교하여 편향 여부를 검토하세요.',
            order=0,
        )
        FileReviewItem.objects.create(
            project_file=f3,
            highlighted_text='GPA 67.1%, 출결 현황 52.4%',
            problem='민감 정보 거부율이 높아 콜드 스타트 해결에 사이드 피처 활용이 제한될 수 있습니다.',
            suggestion='GPA 없이도 작동하는 대체 피처(수강 학점 수, 전공 이수 현황 등)를 설계에 반영하세요.',
            order=1,
        )
        TeamReviewItem.objects.create(
            project_file=f3,
            reviewer=minjun,
            highlighted_text='교수 평판 78.0%, 과목 내용 73.2%',
            problem='교수 평판 데이터를 시스템에서 수집·활용하는 방안이 설계에 반영되어 있지 않습니다.',
            suggestion='에브리타임 강의 평가 크롤링 또는 자체 평가 수집 기능을 백로그에 추가하는 것을 검토하세요.',
        )

        # ── 자료 4: API 설계 명세서 (rejected) ────────────────────
        f4 = ProjectFile.objects.create(
            project=project,
            original_name='REST API 설계 명세서 v0.1',
            file_size=0,
            content=(
                'GET /api/courses — 전체 강의 목록 반환\n'
                'GET /api/recommend — 추천 강의 목록 반환\n'
                'POST /api/user/login — 로그인\n'
                'POST /api/user/register — 회원가입\n\n'
                '인증 방식: 세션 쿠키\n'
                '응답 포맷: JSON\n'
                '에러 처리: HTTP 상태코드만 반환'
            ),
            topic='시스템 설계',
            status='rejected',
            uploaded_by=jiho,
        )
        FileReviewItem.objects.create(
            project_file=f4,
            highlighted_text='인증 방식: 세션 쿠키',
            problem='모바일 클라이언트 확장을 고려하면 세션 쿠키 방식은 stateless하지 않아 확장성이 낮습니다.',
            suggestion='JWT 기반 Bearer 토큰 인증으로 변경하고, 리프레시 토큰 전략을 포함하세요.',
            order=0,
        )
        FileReviewItem.objects.create(
            project_file=f4,
            highlighted_text='에러 처리: HTTP 상태코드만 반환',
            problem='에러 코드만으로는 클라이언트가 오류 원인을 파악할 수 없어 디버깅이 어렵습니다.',
            suggestion='{ "code": "COURSE_NOT_FOUND", "message": "..." } 형태의 표준 에러 응답 스펙을 정의하세요.',
            order=1,
        )
        TeamReview.objects.create(project_file=f4, reviewer=minjun, vote='reject',
                                  comment='전반적으로 스펙이 너무 부실합니다. 요청/응답 예시, 인증 플로우, 에러 스펙을 갖춰서 재제출 해주세요.')
        TeamReview.objects.create(project_file=f4, reviewer=seoyeon, vote='reject',
                                  comment='프론트 개발에 필요한 파라미터 정의가 전혀 없습니다. 재작성 요청합니다.')
        TeamReview.objects.create(project_file=f4, reviewer=yuna, vote='hold',
                                  comment='/api/recommend 엔드포인트의 입력 파라미터와 응답 스키마가 없어 AI 모델 연동이 불가합니다.')

        self.stdout.write(self.style.SUCCESS(
            f'\n더미 데이터 생성 완료!\n'
            f'  프로젝트: {project.name} (코드: {project.join_code})\n'
            f'  유저: minjun / seoyeon / jiho / yuna  (비밀번호: test1234)\n'
            f'  자료: {ProjectFile.objects.count()}건\n'
            f'  일정: {ScheduleEvent.objects.count()}건'
        ))
