from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from accounts.models import FavoriteItem, FavoriteTargetType, UserRole
from analytics.models import LearningFeedback
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
        reflection="",
    ):
        feedback, _ = LearningFeedback.objects.update_or_create(
            user=user,
            course=course,
            defaults={
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
                title="走进人工智能",
                description=(
                    "面向中学生的人工智能专题学习课程，围绕 AI 基本概念、技术基石、社会影响与单元总结展开，"
                    "并配套语音识别、图像识别、AI 对话、在线答题、资源共享和社区交流模块。"
                ),
                status=CourseStatus.PUBLISHED,
                created_by=teacher,
            )
            chapter = self._ensure_chapter(
                course=course,
                order_no=1,
                title="走进人工智能专题学习",
                description="从概念、技术、伦理到总结，共 4 个课时，形成完整的课程闭环。",
            )

            lesson_specs = [
                {
                    "order_no": 1,
                    "title": "什么是人工智能",
                    "estimated_minutes": 45,
                    "is_free_preview": True,
                    "video_url": "https://www.bilibili.com/video/BV1qJ4m1P7N1?p=1",
                    "attachment_url": "https://www.ibm.com/topics/artificial-intelligence",
                    "content": "学习目标：理解人工智能的基本概念，认识生活中的 AI 应用。\n\n文字内容：人工智能是让机器模拟人类感知、思考、学习、判断与决策的技术。我们身边常见的人工智能应用有语音助手、人脸识别、拍照搜题、智能推荐等。通过本节课学习，初步建立对人工智能的基本认知。",
                },
                {
                    "order_no": 2,
                    "title": "人工智能的应用",
                    "estimated_minutes": 45,
                    "video_url": "https://www.bilibili.com/video/BV1Er421773P?p=1",
                    "attachment_url": "https://www.cloudflare.com/learning/ai/what-is-machine-learning/",
                    "content": "学习目标：了解 AI 在医疗、交通、教育、家居等领域的典型应用。\n\n文字内容：人工智能已广泛应用于医疗辅助诊断、自动驾驶、智能导航、个性化教育、智能家居等多个领域，极大提升了社会生产效率与生活便利度。本节课通过案例认识 AI 的实际价值。",
                },
                {
                    "order_no": 3,
                    "title": "人工智能的伦理问题",
                    "estimated_minutes": 45,
                    "video_url": "https://www.bilibili.com/video/BV1Az421m7Wc?p=1",
                    "attachment_url": "https://www.unesco.org/en/artificial-intelligence/recommendation-ethics",
                    "content": "学习目标：了解 AI 带来的隐私安全、算法偏见等伦理问题，树立理性使用观念。\n\n文字内容：AI 在带来便利的同时，也伴随着个人隐私泄露、数据滥用、算法不公平、就业结构变化等伦理与安全问题。我们应辩证看待技术，做到安全、负责、理性地使用人工智能。",
                },
                {
                    "order_no": 4,
                    "title": "人工智能的未来与总结",
                    "estimated_minutes": 45,
                    "video_url": "https://www.bilibili.com/video/BV1vs421N7pf?p=1",
                    "attachment_url": "https://education.microsoft.com/zh-cn/resource/ai",
                    "content": "学习目标：了解 AI 未来发展趋势，完成单元学习总结。\n\n文字内容：未来人工智能将朝着多模态融合、自主学习、人机协同等方向发展。通过本单元四节课的学习，我们认识了 AI 概念、应用、伦理与未来，形成了完整的人工智能认知体系。",
                },
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
                    is_free_preview=item.get("is_free_preview", False),
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

            glossary_terms = [
                (1, "人工智能", "让机器具备感知、推理、学习或生成能力的一类技术总称。"),
                (2, "机器学习", "通过数据训练模型，让系统自动发现规律并完成预测任务。"),
                (3, "深度学习", "使用多层神经网络处理复杂模式识别问题的机器学习方法。"),
                (4, "神经网络", "受生物神经系统启发构建的计算模型，是深度学习的重要基础。"),
                (5, "数据集", "用于训练、验证或测试模型的一组结构化或非结构化数据。"),
                (6, "算法", "解决问题的步骤与规则集合，在 AI 中决定模型学习方式。"),
                (7, "算力", "完成训练和推理所需的计算资源与处理能力。"),
                (8, "模型训练", "让算法在数据中不断调整参数、提升表现的过程。"),
                (9, "推理", "训练完成后，模型根据新输入给出结果的过程。"),
                (10, "语音识别", "将语音信号转换为文本的 AI 应用场景。"),
                (11, "图像识别", "识别图像中的物体、场景或特征信息的技术。"),
                (12, "生成式 AI", "能够生成文本、图像、音频等新内容的人工智能系统。"),
                (13, "算法偏见", "由于数据或设计问题导致模型对部分群体产生不公平结果。"),
                (14, "隐私保护", "在收集、存储和使用数据时保障个人信息安全的要求。"),
                (15, "人机协作", "由人和 AI 各自发挥优势，共同完成任务的工作方式。"),
            ]
            for item in glossary_terms:
                self._ensure_glossary_term(course=course, order_no=item[0], term=item[1], definition=item[2])
            resource_specs = [
                (
                    "生活中的人工智能案例阅读",
                    ResourceType.READING,
                    1,
                    ResourceAudience.ALL,
                    1,
                    "https://www.ibm.com/topics/artificial-intelligence",
                    "案例, 阅读, 第1课",
                    "围绕语音助手、人脸识别、拍照搜题、智能推荐等案例，帮助学生理解生活中的人工智能场景。",
                ),
                (
                    "人工智能发展简史资料",
                    ResourceType.READING,
                    1,
                    ResourceAudience.ALL,
                    2,
                    "https://en.wikipedia.org/wiki/History_of_artificial_intelligence",
                    "历史, 阅读, 第1课",
                    "梳理人工智能发展过程中的关键节点，帮助学生建立基础历史认知。",
                ),
                (
                    "语音识别、图像识别原理简介",
                    ResourceType.COURSEWARE,
                    1,
                    ResourceAudience.ALL,
                    3,
                    "https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API",
                    "语音识别, 图像识别, 第1课",
                    "用简明图文介绍语音识别和图像识别的基本原理，便于后续进入交互体验。",
                ),
                (
                    "AI在各行业应用图文资料",
                    ResourceType.COURSEWARE,
                    2,
                    ResourceAudience.ALL,
                    1,
                    "https://www.cloudflare.com/learning/ai/what-is-ai/",
                    "应用, 图文, 第2课",
                    "概括医疗、交通、教育、家居等领域中人工智能的典型应用场景。",
                ),
                (
                    "典型人工智能产品介绍",
                    ResourceType.READING,
                    2,
                    ResourceAudience.ALL,
                    2,
                    "https://cloud.google.com/vision/docs",
                    "产品, 阅读, 第2课",
                    "介绍常见人工智能产品类型，帮助学生理解技术如何转化为实际服务。",
                ),
                (
                    "AI对话交互使用说明",
                    ResourceType.TOOL,
                    2,
                    ResourceAudience.ALL,
                    3,
                    "https://www.doubao.com/",
                    "AI对话, 工具, 第2课",
                    "说明 AI 对话交互的基本使用方法，引导学生规范体验与观察回答效果。",
                ),
                (
                    "AI隐私安全与伦理案例",
                    ResourceType.READING,
                    3,
                    ResourceAudience.ALL,
                    1,
                    "https://www.unesco.org/en/artificial-intelligence/recommendation-ethics",
                    "伦理, 隐私, 第3课",
                    "通过案例帮助学生认识 AI 使用中的隐私安全与责任边界问题。",
                ),
                (
                    "算法公平性阅读材料",
                    ResourceType.READING,
                    3,
                    ResourceAudience.ALL,
                    2,
                    "https://www.ibm.com/topics/ai-ethics",
                    "公平性, 阅读, 第3课",
                    "围绕算法偏见、公平性与数据质量展开阅读，支撑课堂伦理讨论。",
                ),
                (
                    "科技伦理规范说明",
                    ResourceType.COURSEWARE,
                    3,
                    ResourceAudience.ALL,
                    3,
                    "https://oecd.ai/en/ai-principles",
                    "规范, 伦理, 第3课",
                    "概括负责任使用人工智能的基本原则，帮助学生形成理性使用观念。",
                ),
                (
                    "人工智能未来发展趋势资料",
                    ResourceType.READING,
                    4,
                    ResourceAudience.ALL,
                    1,
                    "https://education.microsoft.com/zh-cn/resource/ai",
                    "未来, 阅读, 第4课",
                    "介绍多模态融合、自主学习、人机协同等人工智能发展趋势。",
                ),
                (
                    "单元知识思维导图",
                    ResourceType.COURSEWARE,
                    4,
                    ResourceAudience.ALL,
                    2,
                    "https://www.mindmeister.com/",
                    "思维导图, 总结, 第4课",
                    "用于整理本单元的概念、应用、伦理与未来四部分知识结构。",
                ),
                (
                    "学习总结与反思模板",
                    ResourceType.COURSEWARE,
                    4,
                    ResourceAudience.ALL,
                    3,
                    "https://www.canva.com/presentations/templates/education/",
                    "总结, 反思, 第4课",
                    "帮助学生完成单元学习总结、个人反思与成果展示准备。",
                ),
            ]
            created_resources = {}
            for title, resource_type, lesson_no, audience, sort_order, external_url, tags, description in resource_specs:
                lesson = lesson_map.get(lesson_no) if lesson_no else None
                created_resources[title] = self._ensure_resource(
                    title=title,
                    description=description,
                    resource_type=resource_type,
                    created_by=teacher,
                    course=course,
                    lesson=lesson,
                    audience=audience,
                    sort_order=sort_order,
                    external_url=external_url,
                    tags=tags,
                )

            guide_specs = [
                {
                    "order_no": 1,
                    "title": "走进人工智能——教学指引",
                    "objectives": "1. 理解人工智能基本概念与典型应用。\n2. 能够使用语音识别、图像识别、AI 对话等交互功能。\n3. 了解人工智能伦理与安全问题，树立正确技术观。\n4. 能够通过网站完成学习、答题、交流、总结全过程。",
                    "key_points": "课程内容 → 交互体验 → 资源库拓展 → 在线答题检测 → 社区交流分享 → 数据看板查看学习情况",
                    "difficult_points": "初中7-9年级学生",
                    "learning_methods": "1. 学生按课时顺序依次学习，观看微课视频。\n2. 每节课完成对应交互体验与练习题。\n3. 拓展内容可在资源库自主学习。\n4. 学习心得与成果可发布至社区交流。\n5. 学习数据可在数据看板查看。",
                    "assignment_suggestion": "共4课时，每课时45分钟",
                    "evaluation_suggestion": "课程围绕人工智能概念、应用、伦理与未来四部分内容展开，适合作为初中阶段的信息科技专题学习单元。",
                },
            ]
            for item in guide_specs:
                self._ensure_guide(course=course, created_by=teacher, **item)
            question_bank = {
                1: [
                    (
                        "人工智能的英文缩写是？",
                        QuestionType.SINGLE_CHOICE,
                        [{"key": "A", "text": "AI"}, {"key": "B", "text": "VR"}, {"key": "C", "text": "AR"}, {"key": "D", "text": "IoT"}],
                        ["A"],
                        "Artificial Intelligence 的常用英文缩写是 AI。",
                    ),
                    (
                        "下列属于人工智能应用的是？",
                        QuestionType.SINGLE_CHOICE,
                        [{"key": "A", "text": "普通计算器"}, {"key": "B", "text": "人脸识别"}, {"key": "C", "text": "笔记本"}, {"key": "D", "text": "台灯"}],
                        ["B"],
                        "人脸识别属于典型的人工智能应用场景。",
                    ),
                ],
                2: [
                    (
                        "AI工作的三大基础不包括？",
                        QuestionType.SINGLE_CHOICE,
                        [{"key": "A", "text": "数据"}, {"key": "B", "text": "算法"}, {"key": "C", "text": "电线"}, {"key": "D", "text": "算力"}],
                        ["C"],
                        "AI 的三大基础通常指数据、算法和算力。",
                    ),
                    (
                        "语音识别的主要作用是？",
                        QuestionType.SINGLE_CHOICE,
                        [{"key": "A", "text": "声音转文字"}, {"key": "B", "text": "文字转声音"}, {"key": "C", "text": "图片转文字"}, {"key": "D", "text": "文字转图片"}],
                        ["A"],
                        "语音识别的核心作用是将语音内容转成文字。",
                    ),
                    (
                        "下列属于AI在交通领域应用的是？",
                        QuestionType.SINGLE_CHOICE,
                        [{"key": "A", "text": "智能音箱"}, {"key": "B", "text": "自动驾驶"}, {"key": "C", "text": "拍照搜题"}, {"key": "D", "text": "药物研发"}],
                        ["B"],
                        "自动驾驶是人工智能在交通领域的典型应用。",
                    ),
                ],
                3: [
                    (
                        "下列属于AI伦理问题的是？",
                        QuestionType.SINGLE_CHOICE,
                        [{"key": "A", "text": "电脑卡顿"}, {"key": "B", "text": "隐私泄露"}, {"key": "C", "text": "屏幕太暗"}, {"key": "D", "text": "键盘失灵"}],
                        ["B"],
                        "隐私泄露属于人工智能使用中需要重点关注的伦理问题。",
                    ),
                    (
                        "关于AI说法正确的是？",
                        QuestionType.SINGLE_CHOICE,
                        [{"key": "A", "text": "AI拥有人类情感"}, {"key": "B", "text": "AI是模拟人类智能的技术"}, {"key": "C", "text": "AI不需要数据"}, {"key": "D", "text": "AI能完全取代人类"}],
                        ["B"],
                        "AI 是模拟人类智能活动的一类技术，而不是拥有人类情感的生命体。",
                    ),
                    (
                        "我们应如何对待人工智能？",
                        QuestionType.SINGLE_CHOICE,
                        [{"key": "A", "text": "完全依赖"}, {"key": "B", "text": "害怕拒绝"}, {"key": "C", "text": "理性、安全、负责任使用"}, {"key": "D", "text": "随意使用"}],
                        ["C"],
                        "面对人工智能，应保持理性、安全和负责任的使用态度。",
                    ),
                ],
                4: [
                    (
                        "本单元“走进人工智能”共有几课时？",
                        QuestionType.SINGLE_CHOICE,
                        [{"key": "A", "text": "2"}, {"key": "B", "text": "4"}, {"key": "C", "text": "6"}, {"key": "D", "text": "8"}],
                        ["B"],
                        "本单元共 4 课时，依次介绍概念、应用、伦理和未来总结。",
                    ),
                    (
                        "学习人工智能最重要的是？",
                        QuestionType.SINGLE_CHOICE,
                        [{"key": "A", "text": "只会使用"}, {"key": "B", "text": "只会体验"}, {"key": "C", "text": "守规则、会思考"}, {"key": "D", "text": "不用学习"}],
                        ["C"],
                        "学习人工智能既要会使用，也要守规则、会思考，形成正确技术观。",
                    ),
                ],
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

            discussion_1 = self._ensure_post(
                title="我身边的人工智能",
                author=student,
                lesson=lesson_map[1],
                category=ForumPostCategory.DISCUSSION,
                content="分享自己生活中遇到的AI应用，如语音助手、刷脸支付、拍照搜题等。",
                is_pinned=True,
            )
            discussion_2 = self._ensure_post(
                title="AI伦理小讨论",
                author=student,
                lesson=lesson_map[3],
                category=ForumPostCategory.DISCUSSION,
                content="你认为使用人工智能时，最需要注意什么问题？",
            )
            discussion_3 = self._ensure_post(
                title="我的学习总结",
                author=student,
                lesson=lesson_map[4],
                category=ForumPostCategory.SHARE,
                content="分享本单元学习收获、体会与反思。",
            )
            showcase_1 = self._ensure_post(
                title="成果展示：我理解的人工智能",
                author=student,
                lesson=lesson_map[4],
                category=ForumPostCategory.SHOWCASE,
                content="本次展示按“概念认知、技术基石、伦理判断、未来展望”四部分展开，并结合语音识别与推荐系统案例说明 AI 如何进入真实生活场景。",
                is_pinned=True,
            )
            showcase_2 = self._ensure_post(
                title="成果展示：AI 应用案例分析卡",
                author=teacher,
                lesson=lesson_map[4],
                category=ForumPostCategory.SHOWCASE,
                content="围绕导航推荐、图像识别和生成式对话三个案例，梳理数据、算法、算力与社会影响之间的联系，可作为课堂展示参考样例。",
            )

            self._ensure_comment(post=discussion_1, author=teacher, content="可以结合语音助手、导航、人脸识别这些具体例子继续补充。")
            self._ensure_comment(post=discussion_2, author=teacher, content="隐私安全和算法公平性都是讨论中很值得展开的方向。")
            self._ensure_comment(post=discussion_3, author=admin, content="这类总结帖很适合整理成答辩展示稿或课堂分享卡片。")
            self._ensure_comment(post=showcase_1, author=teacher, content="结构完整，后续展示时可以再补一个伦理风险案例，让总结更有层次。")
            self._ensure_comment(post=showcase_2, author=student, content="这个案例卡结构很适合直接改成答辩 PPT 页面。")

            for target_post in [discussion_1, discussion_2, discussion_3]:
                self._ensure_like(post=target_post, user=teacher)
            for target_post in [discussion_1, discussion_2, discussion_3]:
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
