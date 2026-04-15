from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from accounts.models import FavoriteItem, FavoriteTargetType, UserRole
from analytics.models import LearningFeedback
from courses.ai_unit_data import (
    COURSE_BLUEPRINT,
    COURSE_GLOSSARY,
    FORUM_DEMO_POSTS,
    GUIDE_BLUEPRINT,
    LESSON_PAGE_DATA,
    LESSON_QUIZ_BANK,
    RESOURCE_LIBRARY,
    SHOWCASE_DEMO_POSTS,
)
from courses.audit import log_content_action
from courses.models import (
    AuditTargetType,
    Chapter,
    Course,
    CourseGlossaryTerm,
    CourseStatus,
    LearningProgress,
    Lesson,
)
from forum.models import ForumComment, ForumPost, ForumPostCategory, ForumPostLike, ForumPostStatus
from guides.models import TeachingGuide
from practice.models import PracticeRecord, PracticeRecordType
from quiz.models import Question, QuestionDifficulty, QuestionType, QuizAnswer, QuizSubmission, WrongQuestion
from resources.models import Resource, ResourceAudience, ResourceType


User = get_user_model()


class Command(BaseCommand):
    help = "Seed polished demo data for the AI course graduation project."

    def add_arguments(self, parser):
        parser.add_argument("--password", default="DemoPass123!", help="Password for all demo users.")
        parser.add_argument(
            "--skip-search-index",
            action="store_true",
            help="Skip search index rebuild after seeding.",
        )

    def _ensure_user(self, *, username, email, password, is_staff, is_superuser, role):
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )
        changed = False
        if user.email != email:
            user.email = email
            changed = True
        if user.is_staff != is_staff:
            user.is_staff = is_staff
            changed = True
        if user.is_superuser != is_superuser:
            user.is_superuser = is_superuser
            changed = True
        user.set_password(password)
        changed = True
        if changed:
            user.save()

        profile = user.profile
        profile.role = role
        profile.school = "示范中学" if role == UserRole.STUDENT else "信息技术教研组"
        profile.major = "人工智能通识" if role == UserRole.STUDENT else "信息技术"
        profile.grade = "高一" if role == UserRole.STUDENT else "教师"
        profile.bio = "用于课程演示与答辩截图的示例账号。"
        profile.save()
        return user

    @staticmethod
    def _ensure_course(*, title, description, status, created_by):
        course, _ = Course.objects.update_or_create(
            title=title,
            created_by=created_by,
            defaults={"description": description, "status": status},
        )
        return course

    @staticmethod
    def _ensure_chapter(*, course, order_no, title, description, is_active=True):
        chapter, _ = Chapter.objects.update_or_create(
            course=course,
            order_no=order_no,
            defaults={
                "title": title,
                "description": description,
                "is_active": is_active,
            },
        )
        return chapter

    @staticmethod
    def _ensure_lesson(
        *,
        chapter,
        order_no,
        title,
        content,
        estimated_minutes,
        video_url="",
        attachment_url="",
        is_free_preview=False,
        is_active=True,
    ):
        lesson, _ = Lesson.objects.update_or_create(
            chapter=chapter,
            order_no=order_no,
            defaults={
                "title": title,
                "content": content,
                "estimated_minutes": estimated_minutes,
                "video_url": video_url,
                "attachment_url": attachment_url,
                "is_free_preview": is_free_preview,
                "is_active": is_active,
            },
        )
        return lesson

    @staticmethod
    def _ensure_glossary_term(*, course, order_no, term, definition):
        CourseGlossaryTerm.objects.update_or_create(
            course=course,
            order_no=order_no,
            defaults={"term": term, "definition": definition},
        )

    @staticmethod
    def _ensure_resource(
        *,
        title,
        description,
        resource_type,
        created_by,
        course,
        lesson=None,
        audience=ResourceAudience.ALL,
        sort_order=1,
        external_url="",
        tags="",
        is_published=True,
    ):
        resource = Resource.objects.filter(title=title, created_by=created_by).first()
        if resource is None:
            resource = Resource(title=title, created_by=created_by)
        resource.description = description
        resource.resource_type = resource_type
        resource.course = course
        resource.lesson = lesson
        resource.audience = audience
        resource.sort_order = sort_order
        resource.external_url = external_url
        resource.tags = tags
        resource.is_published = is_published
        resource.save()
        return resource

    @staticmethod
    def _ensure_guide(
        *,
        course,
        order_no,
        title,
        created_by,
        objectives,
        key_points,
        difficult_points="",
        learning_methods="",
        assignment_suggestion="",
        evaluation_suggestion="",
        unit_name="走进人工智能",
        is_published=True,
    ):
        TeachingGuide.objects.update_or_create(
            course=course,
            order_no=order_no,
            defaults={
                "title": title,
                "unit_name": unit_name,
                "objectives": objectives,
                "key_points": key_points,
                "difficult_points": difficult_points,
                "learning_methods": learning_methods,
                "assignment_suggestion": assignment_suggestion,
                "evaluation_suggestion": evaluation_suggestion,
                "created_by": created_by,
                "is_published": is_published,
            },
        )

    @staticmethod
    def _ensure_question(
        *,
        lesson,
        stem,
        question_type,
        options,
        correct_answer,
        created_by,
        explanation,
        score=5,
        difficulty=QuestionDifficulty.MEDIUM,
    ):
        question, _ = Question.objects.update_or_create(
            lesson=lesson,
            stem=stem,
            defaults={
                "question_type": question_type,
                "options": options,
                "correct_answer": correct_answer,
                "explanation": explanation,
                "score": score,
                "difficulty": difficulty,
                "is_active": True,
                "created_by": created_by,
            },
        )
        return question
    @staticmethod
    def _ensure_post(
        *,
        title,
        author,
        content,
        category,
        lesson=None,
        status=ForumPostStatus.PUBLISHED,
        is_pinned=False,
        is_solved=False,
    ):
        post, _ = ForumPost.objects.update_or_create(
            title=title,
            defaults={
                "author": author,
                "content": content,
                "lesson": lesson,
                "category": category,
                "status": status,
                "is_pinned": is_pinned,
                "is_solved": is_solved,
            },
        )
        return post

    @staticmethod
    def _ensure_comment(*, post, author, content, parent=None):
        comment, _ = ForumComment.objects.update_or_create(
            post=post,
            author=author,
            content=content,
            defaults={"parent": parent, "is_deleted": False},
        )
        return comment

    @staticmethod
    def _ensure_like(*, post, user):
        ForumPostLike.objects.get_or_create(post=post, user=user)

    @staticmethod
    def _ensure_progress(*, user, lesson, view_count, completed):
        progress, _ = LearningProgress.objects.get_or_create(user=user, lesson=lesson)
        progress.view_count = view_count
        progress.completed = completed
        progress.completed_at = timezone.now() if completed else None
        progress.save(update_fields=["view_count", "completed", "completed_at", "last_viewed_at"])
        return progress

    @staticmethod
    def _ensure_feedback(
        *,
        user,
        course,
        concept_score,
        mechanism_score,
        ethics_score,
        expression_score,
        exploration_score,
        student_name="",
        class_name="",
        knowledge_q1="",
        knowledge_q2="",
        knowledge_q3="",
        knowledge_q4="",
        practice_q5="",
        practice_q6="",
        practice_q7="",
        attitude_q8="",
        attitude_q9="",
        attitude_q10="",
        reflection_gain="",
        reflection_gap="",
        reflection_advice="",
        overall_level="",
        reflection="",
    ):
        feedback, _ = LearningFeedback.objects.update_or_create(
            user=user,
            course=course,
            defaults={
                "student_name": student_name,
                "class_name": class_name,
                "knowledge_q1": knowledge_q1,
                "knowledge_q2": knowledge_q2,
                "knowledge_q3": knowledge_q3,
                "knowledge_q4": knowledge_q4,
                "practice_q5": practice_q5,
                "practice_q6": practice_q6,
                "practice_q7": practice_q7,
                "attitude_q8": attitude_q8,
                "attitude_q9": attitude_q9,
                "attitude_q10": attitude_q10,
                "reflection_gain": reflection_gain,
                "reflection_gap": reflection_gap,
                "reflection_advice": reflection_advice,
                "overall_level": overall_level,
                "concept_score": concept_score,
                "mechanism_score": mechanism_score,
                "ethics_score": ethics_score,
                "expression_score": expression_score,
                "exploration_score": exploration_score,
                "reflection": reflection,
            },
        )
        return feedback

    @staticmethod
    def _ensure_practice_record(*, user, practice_type, input_text="", output_text="", metadata=None):
        PracticeRecord.objects.update_or_create(
            user=user,
            practice_type=practice_type,
            input_text=input_text,
            defaults={
                "output_text": output_text,
                "metadata": metadata or {},
            },
        )

    @staticmethod
    def _ensure_favorite(*, user, target_type, target_id, title_snapshot, url_snapshot):
        FavoriteItem.objects.update_or_create(
            user=user,
            target_type=target_type,
            target_id=target_id,
            defaults={
                "title_snapshot": title_snapshot,
                "url_snapshot": url_snapshot,
            },
        )

    def handle(self, *args, **options):
        password = options["password"]
        skip_search_index = bool(options["skip_search_index"])

        with transaction.atomic():
            teacher = self._ensure_user(
                username="demo_teacher",
                email="demo_teacher@example.com",
                password=password,
                is_staff=False,
                is_superuser=False,
                role=UserRole.TEACHER,
            )
            student = self._ensure_user(
                username="demo_student",
                email="demo_student@example.com",
                password=password,
                is_staff=False,
                is_superuser=False,
                role=UserRole.STUDENT,
            )
            admin = self._ensure_user(
                username="demo_admin",
                email="demo_admin@example.com",
                password=password,
                is_staff=True,
                is_superuser=True,
                role=UserRole.ADMIN,
            )

            course = self._ensure_course(
                title=COURSE_BLUEPRINT["title"],
                description=COURSE_BLUEPRINT["description"],
                status=CourseStatus.PUBLISHED,
                created_by=teacher,
            )
            chapter = self._ensure_chapter(
                course=course,
                order_no=1,
                title=COURSE_BLUEPRINT["chapter_title"],
                description=COURSE_BLUEPRINT["chapter_description"],
            )

            lesson_specs = [
                {
                    "order_no": order_no,
                    "title": item["title"],
                    "estimated_minutes": item["estimated_minutes"],
                    "video_url": item["video_url"],
                    "attachment_url": item["attachment_url"],
                    "content": item["content"],
                }
                for order_no, item in sorted(LESSON_PAGE_DATA.items())
            ]
            lessons = [
                self._ensure_lesson(
                    chapter=chapter,
                    order_no=item["order_no"],
                    title=item["title"],
                    content=item["content"],
                    estimated_minutes=item["estimated_minutes"],
                    video_url=item["video_url"],
                    attachment_url=item["attachment_url"],
                    is_free_preview=False,
                )
                for item in lesson_specs
            ]
            lesson_map = {lesson.order_no: lesson for lesson in lessons}

            Resource.objects.filter(course=course, created_by=teacher).delete()
            TeachingGuide.objects.filter(course=course).delete()
            ForumPost.objects.filter(lesson__chapter__course=course, author__in=[teacher, student, admin]).delete()
            Question.objects.filter(lesson__chapter__course=course).delete()
            LearningProgress.objects.filter(user=student, lesson__chapter__course=course).delete()
            QuizSubmission.objects.filter(user=student, lesson__chapter__course=course).delete()
            WrongQuestion.objects.filter(user=student, question__lesson__chapter__course=course).delete()
            LearningFeedback.objects.filter(user=student, course=course).delete()
            FavoriteItem.objects.filter(user=student).delete()

            for item in COURSE_GLOSSARY:
                self._ensure_glossary_term(course=course, order_no=item[0], term=item[1], definition=item[2])

            resource_type_map = {
                "reading": ResourceType.READING,
                "courseware": ResourceType.COURSEWARE,
                "tool": ResourceType.TOOL,
                "video": ResourceType.VIDEO,
            }
            created_resources = {}
            for item in RESOURCE_LIBRARY:
                lesson = lesson_map.get(item["lesson_no"]) if item.get("lesson_no") else None
                created_resources[item["title"]] = self._ensure_resource(
                    title=item["title"],
                    description=item["description"],
                    resource_type=resource_type_map[item["resource_type"]],
                    created_by=teacher,
                    course=course,
                    lesson=lesson,
                    audience=ResourceAudience.ALL,
                    sort_order=item["sort_order"],
                    external_url=item["external_url"],
                    tags=item["tags"],
                )

            self._ensure_guide(
                course=course,
                created_by=teacher,
                order_no=1,
                title=GUIDE_BLUEPRINT["title"],
                objectives=GUIDE_BLUEPRINT["objectives"],
                key_points=GUIDE_BLUEPRINT["key_points"],
                difficult_points=GUIDE_BLUEPRINT["difficult_points"],
                learning_methods=GUIDE_BLUEPRINT["learning_methods"],
                assignment_suggestion=GUIDE_BLUEPRINT["assignment_suggestion"],
                evaluation_suggestion=GUIDE_BLUEPRINT["evaluation_suggestion"],
                unit_name=GUIDE_BLUEPRINT["unit_name"],
            )

            question_bank = {
                lesson_no: [
                    (
                        question["stem"],
                        QuestionType.SINGLE_CHOICE,
                        question["options"],
                        [question["answer"]],
                        question["explanation"],
                    )
                    for question in questions
                ]
                for lesson_no, questions in LESSON_QUIZ_BANK.items()
            }
            lesson_questions = {}
            for lesson_no, rows in question_bank.items():
                lesson_questions[lesson_no] = []
                for stem, question_type, options_list, correct_answer, explanation in rows:
                    lesson_questions[lesson_no].append(
                        self._ensure_question(
                            lesson=lesson_map[lesson_no],
                            stem=stem,
                            question_type=question_type,
                            options=options_list,
                            correct_answer=correct_answer,
                            created_by=teacher,
                            explanation=explanation,
                            difficulty=QuestionDifficulty.MEDIUM,
                        )
                    )

            category_map = {
                "discussion": ForumPostCategory.DISCUSSION,
                "share": ForumPostCategory.SHARE,
                "showcase": ForumPostCategory.SHOWCASE,
            }
            demo_posts = {}
            for spec in FORUM_DEMO_POSTS:
                demo_posts[spec["title"]] = self._ensure_post(
                    title=spec["title"],
                    author=student,
                    lesson=lesson_map[spec["lesson_no"]],
                    category=category_map[spec["category"]],
                    content=spec["content"],
                    is_pinned=spec["is_pinned"],
                )
            demo_showcases = {}
            for spec in SHOWCASE_DEMO_POSTS:
                author = student if spec["is_pinned"] else teacher
                demo_showcases[spec["title"]] = self._ensure_post(
                    title=spec["title"],
                    author=author,
                    lesson=lesson_map[spec["lesson_no"]],
                    category=category_map[spec["category"]],
                    content=spec["content"],
                    is_pinned=spec["is_pinned"],
                )

            discussion_1 = demo_posts["我身边的人工智能"]
            discussion_2 = demo_posts["AI 伦理小讨论"]
            discussion_3 = demo_posts["我的学习总结"]
            showcase_1 = demo_showcases["成果展示：我理解的人工智能"]
            showcase_2 = demo_showcases["成果展示：AI 应用观察卡"]

            self._ensure_comment(post=discussion_1, author=teacher, content="可以继续补充语音助手、导航推荐和拍照搜题这些具体案例。")
            self._ensure_comment(post=discussion_2, author=teacher, content="可以从隐私安全、深度伪造和责任边界三个角度继续展开。")
            self._ensure_comment(post=discussion_3, author=admin, content="这类总结帖很适合进一步整理成课堂汇报或答辩展示稿。")
            self._ensure_comment(post=showcase_1, author=teacher, content="结构完整，后续可再补一个伦理风险案例，让展示层次更丰富。")
            self._ensure_comment(post=showcase_2, author=student, content="这张观察卡很适合直接延展为 PPT 的案例分析页面。")

            for target_post in [discussion_1, discussion_2, discussion_3]:
                self._ensure_like(post=target_post, user=teacher)
                self._ensure_like(post=target_post, user=student)
            for target_post in [discussion_1, discussion_3]:
                self._ensure_like(post=target_post, user=admin)
            for target_post in [showcase_1, showcase_2]:
                self._ensure_like(post=target_post, user=teacher)
                self._ensure_like(post=target_post, user=student)

            self._ensure_progress(user=student, lesson=lesson_map[1], view_count=5, completed=True)
            self._ensure_progress(user=student, lesson=lesson_map[2], view_count=4, completed=True)
            self._ensure_progress(user=student, lesson=lesson_map[3], view_count=3, completed=True)
            self._ensure_progress(user=student, lesson=lesson_map[4], view_count=2, completed=True)
            self._ensure_feedback(
                user=student,
                course=course,
                concept_score=4,
                mechanism_score=4,
                ethics_score=4,
                expression_score=4,
                exploration_score=5,
                student_name="演示学生",
                class_name="七年级 1 班",
                knowledge_q1="A",
                knowledge_q2="B",
                knowledge_q3="A",
                knowledge_q4="B",
                practice_q5="B",
                practice_q6="B",
                practice_q7="A",
                attitude_q8="A",
                attitude_q9="B",
                attitude_q10="A",
                reflection_gain="已经能够从概念、应用、伦理和未来四个角度理解人工智能。",
                reflection_gap="还想继续加强对数据、算法、算力关系的解释能力。",
                reflection_advice="希望后续增加更多贴近校园生活的 AI 案例与课堂演示。",
                overall_level="good",
                reflection="已经能够从概念、应用、伦理和未来四个角度理解人工智能，下一步想把单元内容整理成更完整的展示稿。",
            )
            QuizSubmission.objects.filter(user=student, lesson__chapter__course=course).delete()
            WrongQuestion.objects.filter(user=student, question__lesson__chapter__course=course).delete()

            unit_questions = lesson_questions[1] + lesson_questions[2] + lesson_questions[3] + lesson_questions[4]
            submission_1 = QuizSubmission.objects.create(
                user=student,
                lesson=lesson_map[4],
                total_questions=10,
                correct_count=8,
                total_score=50,
                earned_score=40,
                accuracy=80,
            )
            for question in unit_questions[:4] + unit_questions[5:9]:
                QuizAnswer.objects.create(
                    submission=submission_1,
                    question=question,
                    user_answer=question.correct_answer,
                    expected_answer=question.correct_answer,
                    is_correct=True,
                    score_awarded=question.score,
                    explanation_snapshot=question.explanation,
                )
            wrong_question = unit_questions[4]
            QuizAnswer.objects.create(
                submission=submission_1,
                question=wrong_question,
                user_answer=["A"],
                expected_answer=wrong_question.correct_answer,
                is_correct=False,
                score_awarded=0,
                explanation_snapshot=wrong_question.explanation,
            )
            WrongQuestion.objects.create(user=student, question=wrong_question, wrong_count=1, resolved=False)
            second_wrong_question = unit_questions[9]
            QuizAnswer.objects.create(
                submission=submission_1,
                question=second_wrong_question,
                user_answer=["A"],
                expected_answer=second_wrong_question.correct_answer,
                is_correct=False,
                score_awarded=0,
                explanation_snapshot=second_wrong_question.explanation,
            )
            WrongQuestion.objects.create(user=student, question=second_wrong_question, wrong_count=1, resolved=False)

            self._ensure_practice_record(
                user=student,
                practice_type=PracticeRecordType.DIALOGUE,
                input_text="人工智能为什么离不开数据？",
                output_text="因为数据为模型提供学习样本，没有足够数据，模型就难以形成稳定规律。",
                metadata={"source": "seed_demo_data", "lesson": 2},
            )
            self._ensure_practice_record(
                user=student,
                practice_type=PracticeRecordType.SPEECH,
                input_text="今天天气怎么样，顺便介绍一下人工智能。",
                output_text="已记录语音识别结果，并可继续分析识别准确率。",
                metadata={"source": "seed_demo_data", "lesson": 2},
            )
            self._ensure_practice_record(
                user=student,
                practice_type=PracticeRecordType.IMAGE,
                output_text="识别标签：界面截图、文字较多、亮度较高。",
                metadata={
                    "format": "PNG",
                    "width": 1365,
                    "height": 768,
                    "orientation": "横向",
                    "brightness": 182.5,
                    "labels": ["界面截图", "文字较多", "亮度较高"],
                    "source": "seed_demo_data",
                },
            )

            guide_1 = TeachingGuide.objects.get(course=course, order_no=1)
            self._ensure_favorite(
                user=student,
                target_type=FavoriteTargetType.COURSE,
                target_id=course.id,
                title_snapshot=course.title,
                url_snapshot=reverse("courses:course_detail", kwargs={"slug": course.slug}),
            )
            self._ensure_favorite(
                user=student,
                target_type=FavoriteTargetType.RESOURCE,
                target_id=created_resources["单元知识思维导图"].id,
                title_snapshot="单元知识思维导图",
                url_snapshot=created_resources["单元知识思维导图"].get_absolute_url(),
            )
            self._ensure_favorite(
                user=student,
                target_type=FavoriteTargetType.POST,
                target_id=discussion_1.id,
                title_snapshot=discussion_1.title,
                url_snapshot=reverse("forum:post_detail", kwargs={"post_id": discussion_1.id}),
            )
            self._ensure_favorite(
                user=student,
                target_type=FavoriteTargetType.GUIDE,
                target_id=guide_1.id,
                title_snapshot=guide_1.title,
                url_snapshot=guide_1.get_absolute_url(),
            )

            log_content_action(
                actor=teacher,
                target_type=AuditTargetType.COURSE,
                target_id=course.id,
                action="seed",
                message="初始化课程《走进人工智能》示例数据。",
                course=course,
            )
            log_content_action(
                actor=teacher,
                target_type=AuditTargetType.LESSON,
                target_id=lesson_map[2].id,
                action="seed",
                message="写入第2课时的资源、题目和互动演示数据。",
                course=course,
                chapter=chapter,
                lesson=lesson_map[2],
            )
            log_content_action(
                actor=teacher,
                target_type=AuditTargetType.QUESTION,
                target_id=lesson_questions[3][0].id,
                action="seed",
                message="写入第3课时题库与错题演示数据。",
                course=course,
                chapter=chapter,
                lesson=lesson_map[3],
            )

        if not skip_search_index:
            call_command("rebuild_search_index")

        self.stdout.write(self.style.SUCCESS("AI demo data seeding completed."))
        self.stdout.write("Users created or updated:")
        self.stdout.write("  demo_teacher (teacher)")
        self.stdout.write("  demo_student (student)")
        self.stdout.write("  demo_admin (admin / superuser)")
        self.stdout.write(f"Password: {password}")



