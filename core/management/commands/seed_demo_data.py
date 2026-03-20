from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from accounts.models import FavoriteItem, FavoriteTargetType, UserRole
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
                    "title": "第1课时 人工智能是什么",
                    "estimated_minutes": 18,
                    "is_free_preview": True,
                    "video_url": "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
                    "attachment_url": "https://www.ibm.com/topics/artificial-intelligence",
                    "content": "课程概述：本课时从“什么是人工智能”切入，说明人工智能并不是神秘黑箱，而是让机器表现出感知、判断、学习和生成能力的技术集合。\n\n重点内容：1. 区分人工智能、机器学习与深度学习的关系。2. 通过推荐系统、语音助手、人脸识别等生活案例认识 AI。3. 用时间线梳理图灵测试、专家系统、机器学习浪潮与生成式 AI 的发展。\n\n学习任务：观察生活中的一个 AI 场景，尝试说明它输入了什么数据、输出了什么结果。",
                },
                {
                    "order_no": 2,
                    "title": "第2课时 数据、算法与算力",
                    "estimated_minutes": 22,
                    "video_url": "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
                    "attachment_url": "https://www.cloudflare.com/learning/ai/what-is-machine-learning/",
                    "content": "单元导学：理解 AI 为什么能“学会”任务，关键在于数据、算法和算力三者协同工作。\n\n重点内容：1. 数据像教材，为模型提供经验。2. 算法像方法，决定机器如何从数据中提炼规律。3. 算力像发动机，决定训练和推理效率。\n\n学习任务：以语音识别为例，分析如果缺少高质量语音数据、合适算法或足够算力，会出现什么问题。",
                },
                {
                    "order_no": 3,
                    "title": "第3课时 AI 的社会影响与伦理",
                    "estimated_minutes": 20,
                    "video_url": "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
                    "attachment_url": "https://www.unesco.org/en/artificial-intelligence/recommendation-ethics",
                    "content": "课程目标：认识 AI 带来便利的同时，也可能引发隐私泄露、算法偏见、虚假生成和就业结构变化等问题。\n\n重点内容：1. AI 在医疗、教育、交通中的积极价值。2. 数据偏见如何导致不公平结果。3. 面对 AI 工具时，为什么仍然需要人的判断和责任承担。\n\n学习任务：阅读一个 AI 伦理案例后，尝试从开发者、平台和用户三个角色分析责任边界。",
                },
                {
                    "order_no": 4,
                    "title": "第4课时 单元总结与未来展望",
                    "estimated_minutes": 16,
                    "video_url": "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4",
                    "attachment_url": "https://education.microsoft.com/zh-cn/resource/ai",
                    "content": "单元总结：回顾人工智能的概念、技术基石和社会影响，形成知识思维导图。\n\n重点内容：1. 用“概念-技术-应用-伦理”框架整理课程知识。2. 结合个人兴趣，思考未来可继续探索的 AI 方向。3. 为成果展示或课堂汇报准备结构化表达。\n\n学习任务：完成一页学习成果展示，概括最重要的知识点和个人观察。",
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
                ("AI 概念导入动画", ResourceType.VIDEO, 1, ResourceAudience.ALL, 1, "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4", "视频, 导入, 概念", "用于第1课时导入，帮助学生快速建立对人工智能的直观认识。"),
                ("AI 发展简史阅读卡", ResourceType.READING, 1, ResourceAudience.ALL, 2, "https://www.ibm.com/topics/artificial-intelligence", "阅读, 历史, 概念", "梳理人工智能从早期研究到生成式 AI 的关键节点。"),
                ("生活中的 AI 应用图解", ResourceType.COURSEWARE, 1, ResourceAudience.ALL, 3, "https://www.cloudflare.com/learning/ai/what-is-ai/", "图解, 案例, 生活应用", "用图文方式展示推荐系统、导航、刷脸支付等典型应用。"),
                ("图灵测试案例页", ResourceType.READING, 1, ResourceAudience.ALL, 4, "https://en.wikipedia.org/wiki/Turing_test", "图灵测试, 阅读", "帮助学生理解“机器像不像人在思考”这一经典问题。"),
                ("机器学习原理动画", ResourceType.VIDEO, 2, ResourceAudience.ALL, 1, "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4", "视频, 机器学习", "作为第2课时导入视频，说明模型如何从样本中学习规律。"),
                ("语音识别原理科普", ResourceType.READING, 2, ResourceAudience.ALL, 2, "https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API", "语音识别, 阅读", "介绍从采集语音到转写文本的基本流程。"),
                ("图像识别原理科普", ResourceType.READING, 2, ResourceAudience.ALL, 3, "https://cloud.google.com/vision/docs", "图像识别, 阅读", "介绍图像分类和目标识别的常见任务。"),
                ("数据-算法-算力三角图", ResourceType.COURSEWARE, 2, ResourceAudience.ALL, 4, "https://www.nvidia.com/en-us/glossary/data-science/", "数据, 算法, 算力", "用一张图说明 AI 三大技术基石之间的关系。"),
                ("算力发展小视频", ResourceType.VIDEO, 2, ResourceAudience.ALL, 5, "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4", "视频, 算力", "用于说明算力提升如何推动 AI 应用落地。"),
                ("AI 伦理案例动画", ResourceType.VIDEO, 3, ResourceAudience.ALL, 1, "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4", "视频, 伦理", "通过案例动画导入算法偏见与责任问题。"),
                ("AI 隐私问题阅读", ResourceType.READING, 3, ResourceAudience.ALL, 2, "https://www.unesco.org/en/artificial-intelligence/recommendation-ethics", "隐私, 阅读", "帮助学生理解数据采集与个人信息保护之间的张力。"),
                ("算法偏见案例文章", ResourceType.READING, 3, ResourceAudience.ALL, 3, "https://www.ibm.com/topics/ai-ethics", "算法偏见, 伦理", "通过真实案例理解偏见为何会进入模型。"),
                ("AI 辩论素材包", ResourceType.COURSEWARE, 3, ResourceAudience.ALL, 4, "https://www.unesco.org/en/artificial-intelligence", "辩论, 素材包", "支持课堂开展“AI 会不会取代人类工作”的辩论活动。"),
                ("AI 治理案例清单", ResourceType.COURSEWARE, 3, ResourceAudience.ALL, 5, "https://oecd.ai/en/ai-principles", "治理, 案例", "汇总国际上关于负责任 AI 的原则与案例。"),
                ("单元知识思维导图", ResourceType.COURSEWARE, 4, ResourceAudience.ALL, 1, "https://www.mindmeister.com/", "思维导图, 总结", "帮助学生完成全单元知识梳理。"),
                ("成果展示 PPT 模板", ResourceType.COURSEWARE, 4, ResourceAudience.ALL, 2, "https://www.canva.com/presentations/templates/education/", "模板, 汇报", "用于课程成果展示与答辩演示截图。"),
                ("单元总结微课视频", ResourceType.VIDEO, 4, ResourceAudience.ALL, 3, "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4", "总结, 视频", "用于第4课时收束，帮助学生回看整单元重点。"),
                ("豆包体验入口", ResourceType.TOOL, 0, ResourceAudience.ALL, 1, "https://www.doubao.com/", "工具, AI 对话", "推荐学生体验中文大模型对话。"),
                ("通义千问体验入口", ResourceType.TOOL, 0, ResourceAudience.ALL, 2, "https://tongyi.aliyun.com/", "工具, AI 对话", "作为综合在线体验工具，扩展学生视野。"),
                ("文心一言体验入口", ResourceType.TOOL, 0, ResourceAudience.ALL, 3, "https://yiyan.baidu.com/", "工具, 文本生成", "用于对比不同 AI 问答系统的回答风格。"),
                ("AI 职业方向介绍", ResourceType.READING, 0, ResourceAudience.ALL, 4, "https://www.ibm.com/careers/artificial-intelligence", "职业, 拓展阅读", "介绍 AI 产品经理、算法工程师、数据标注等岗位。"),
                ("AIGC 安全使用清单", ResourceType.READING, 0, ResourceAudience.ALL, 5, "https://www.microsoft.com/ai/responsible-ai", "安全, 使用规范", "帮助学生建立规范使用生成式 AI 的意识。"),
                ("课堂讨论任务单", ResourceType.COURSEWARE, 2, ResourceAudience.TEACHER, 90, "https://education.microsoft.com/", "教师, 讨论组织", "教师专用资源，用于组织第2课时的小组讨论。"),
                ("AI 伦理评价量规模板", ResourceType.COURSEWARE, 3, ResourceAudience.TEACHER, 91, "https://www.canva.com/", "教师, 评价模板", "教师专用资源，用于对学生伦理讨论成果进行过程性评价。"),
                ("单元项目展示评分表", ResourceType.READING, 4, ResourceAudience.TEACHER, 92, "https://education.google.com/", "教师, 评分表", "教师专用资源，用于第4课时成果展示评分。"),
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
                    "title": "单元教学目标与学情定位",
                    "objectives": "知识目标：理解人工智能基本概念与典型应用。\n技能目标：能够用数据、算法、算力解释 AI 工作机制。\n情感目标：形成对 AI 价值与风险并重的理性认识。",
                    "key_points": "课程导入、生活案例连接、四课时学习路径设计。",
                    "difficult_points": "帮助学生区分人工智能、机器学习与生成式 AI。",
                    "learning_methods": "采用案例导入、图解讲授与情境提问结合的方式。",
                    "assignment_suggestion": "请学生课后记录一个身边的 AI 场景并拍照或截图说明。",
                    "evaluation_suggestion": "可通过课堂提问、学习单填写和生活案例描述三种方式进行形成性评价。",
                },
                {
                    "order_no": 2,
                    "title": "课时重难点与课堂组织建议",
                    "objectives": "围绕四课时分别明确概念理解、技术分析、伦理讨论与成果表达目标。",
                    "key_points": "第1课重概念，第2课重机制，第3课重判断，第4课重总结。",
                    "difficult_points": "第2课时学生容易把数据、算法、算力混为一谈；第3课时容易只谈观点不举例。",
                    "learning_methods": "建议采用小组讨论、板书共建和案例拆解的方式推进。",
                    "assignment_suggestion": "课后布置一页图文总结，要求包含关键词和生活实例。",
                    "evaluation_suggestion": "可设置“概念是否准确、案例是否贴切、表达是否清晰”三项课堂观察指标。",
                },
                {
                    "order_no": 3,
                    "title": "互动实践实施建议",
                    "objectives": "引导学生通过语音识别、图像识别、AI 对话和在线答题完成“体验式学习”。",
                    "key_points": "每 5-8 分钟插入一个交互节点，保持注意力与参与度。",
                    "difficult_points": "学生容易把互动体验当作娱乐，需要教师及时回扣知识点。",
                    "learning_methods": "先操作体验，再追问原理，最后回到课程知识结构。",
                    "assignment_suggestion": "要求学生至少完成 1 次 AI 对话体验并写出对回答质量的评价。",
                    "evaluation_suggestion": "根据体验记录、答题正确率和反思文字评价学生实践效果。",
                },
                {
                    "order_no": 4,
                    "title": "学习评价与成果展示建议",
                    "objectives": "帮助教师从知识掌握、实践表现、合作表达三方面综合评价学习效果。",
                    "key_points": "终结性评价应结合成果展示，避免只看选择题成绩。",
                    "difficult_points": "评价标准需要兼顾准确性、思辨性与表达能力。",
                    "learning_methods": "采用“自评 + 同伴互评 + 教师评价”三元结合方式。",
                    "assignment_suggestion": "组织学生用 PPT 或海报展示“我理解的人工智能”。",
                    "evaluation_suggestion": "建议设置四个维度：概念理解 30%、实践完成度 25%、案例分析 25%、表达展示 20%。",
                },
            ]
            for item in guide_specs:
                self._ensure_guide(course=course, created_by=teacher, **item)
            question_bank = {
                1: [
                    ("人工智能更强调机器具备哪一类能力？", QuestionType.SINGLE_CHOICE, [{"key": "A", "text": "机械重复"}, {"key": "B", "text": "感知与判断"}, {"key": "C", "text": "完全随机"}, {"key": "D", "text": "只会计算"}], ["B"], "人工智能强调感知、推理、学习与生成等能力。"),
                    ("以下哪些属于生活中的 AI 应用？", QuestionType.MULTIPLE_CHOICE, [{"key": "A", "text": "短视频推荐"}, {"key": "B", "text": "语音助手"}, {"key": "C", "text": "人脸解锁"}, {"key": "D", "text": "普通尺子"}], ["A", "B", "C"], "推荐系统、语音助手和人脸解锁都属于常见 AI 应用。"),
                    ("图灵测试常被用来讨论机器是否表现出类似人类的智能。", QuestionType.TRUE_FALSE, [{"key": "A", "text": "正确"}, {"key": "B", "text": "错误"}], ["A"], "图灵测试是人工智能发展史上的经典概念。"),
                    ("生成式 AI 与传统检索系统相比，最大的特点是？", QuestionType.SINGLE_CHOICE, [{"key": "A", "text": "只能背诵资料"}, {"key": "B", "text": "能够生成新内容"}, {"key": "C", "text": "完全不需要数据"}, {"key": "D", "text": "只能离线运行"}], ["B"], "生成式 AI 可以生成文本、图像、音频等内容。"),
                    ("人工智能的发展不需要数据支持。", QuestionType.TRUE_FALSE, [{"key": "A", "text": "正确"}, {"key": "B", "text": "错误"}], ["B"], "数据是很多 AI 系统学习和推理的基础。"),
                ],
                2: [
                    ("下列哪一项不属于 AI 的三大技术基石？", QuestionType.SINGLE_CHOICE, [{"key": "A", "text": "数据"}, {"key": "B", "text": "算法"}, {"key": "C", "text": "算力"}, {"key": "D", "text": "运气"}], ["D"], "数据、算法和算力是 AI 的三大技术基石。"),
                    ("训练一个图像识别模型通常需要哪些要素？", QuestionType.MULTIPLE_CHOICE, [{"key": "A", "text": "标注数据"}, {"key": "B", "text": "学习算法"}, {"key": "C", "text": "计算资源"}, {"key": "D", "text": "完全手写规则"}], ["A", "B", "C"], "图像识别模型通常需要数据、算法与算力配合。"),
                    ("算力越高，就一定能得到完全正确的 AI 结果。", QuestionType.TRUE_FALSE, [{"key": "A", "text": "正确"}, {"key": "B", "text": "错误"}], ["B"], "算力重要，但数据质量和算法设计同样关键。"),
                    ("语音识别系统输出的最终结果通常是什么？", QuestionType.SINGLE_CHOICE, [{"key": "A", "text": "一段文字"}, {"key": "B", "text": "一张图片"}, {"key": "C", "text": "一段代码"}, {"key": "D", "text": "随机符号"}], ["A"], "语音识别的目标通常是将语音转换为文本。"),
                    ("机器学习的核心思想更接近以下哪一项？", QuestionType.SINGLE_CHOICE, [{"key": "A", "text": "完全手工编写每条规则"}, {"key": "B", "text": "让系统通过样本学习规律"}, {"key": "C", "text": "只靠硬件升级"}, {"key": "D", "text": "只依赖网络速度"}], ["B"], "机器学习强调从数据中自动学习。"),
                ],
                3: [
                    ("算法偏见属于 AI 伦理问题的一部分。", QuestionType.TRUE_FALSE, [{"key": "A", "text": "正确"}, {"key": "B", "text": "错误"}], ["A"], "算法偏见会影响公平性，因此属于伦理问题。"),
                    ("以下哪项更接近 AI 隐私风险？", QuestionType.SINGLE_CHOICE, [{"key": "A", "text": "未经同意收集人脸数据"}, {"key": "B", "text": "显示器尺寸不同"}, {"key": "C", "text": "鼠标颜色变化"}, {"key": "D", "text": "键盘布局调整"}], ["A"], "未经同意采集和使用个人数据会带来隐私风险。"),
                    ("负责任的 AI 一般强调哪些原则？", QuestionType.MULTIPLE_CHOICE, [{"key": "A", "text": "公平"}, {"key": "B", "text": "透明"}, {"key": "C", "text": "安全"}, {"key": "D", "text": "越神秘越好"}], ["A", "B", "C"], "公平、透明和安全是常见的负责任 AI 原则。"),
                    ("面对 AI 工具，人类更适合承担哪一项角色？", QuestionType.SINGLE_CHOICE, [{"key": "A", "text": "完全放弃判断"}, {"key": "B", "text": "负责监督和决策"}, {"key": "C", "text": "永远不用工具"}, {"key": "D", "text": "只做重复劳动"}], ["B"], "人机协作中，人类仍应承担监督、判断和责任。"),
                    ("AI 会完全、立刻取代所有工作岗位。", QuestionType.TRUE_FALSE, [{"key": "A", "text": "正确"}, {"key": "B", "text": "错误"}], ["B"], "AI 会改变岗位结构，但并不意味着立刻取代所有工作。"),
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
                title="我身边最典型的 AI 应用是什么？",
                author=student,
                lesson=lesson_map[1],
                category=ForumPostCategory.DISCUSSION,
                content="本课学完后，发现短视频推荐、导航、拍照美颜都在使用 AI。最明显的感受是，AI 让服务越来越“懂我”，但也会让我担心信息茧房。",
                is_pinned=True,
            )
            discussion_2 = self._ensure_post(
                title="语音识别为什么离不开大量数据？",
                author=student,
                lesson=lesson_map[2],
                category=ForumPostCategory.HELP,
                content="体验语音识别后发现，同一句话不同人读出来差别很大。是不是因为模型必须见过大量不同口音、速度和环境噪声的数据，才能做出更稳定的判断？",
                is_solved=True,
            )
            discussion_3 = self._ensure_post(
                title="AI 会取代人类工作吗？",
                author=teacher,
                lesson=lesson_map[3],
                category=ForumPostCategory.DISCUSSION,
                content="欢迎围绕第3课时案例进行讨论：哪些工作会被 AI 明显改变？哪些工作依然高度依赖人的判断、共情与责任承担？",
            )
            note_1 = self._ensure_post(
                title="学习笔记：人工智能并不神秘",
                author=student,
                lesson=lesson_map[1],
                category=ForumPostCategory.SHARE,
                content="我的理解是，人工智能不等于什么都会的机器人，而是一组完成具体任务的技术。真正重要的是它背后的数据、算法和目标。",
            )
            note_2 = self._ensure_post(
                title="学习笔记：数据、算法、算力的关系",
                author=student,
                lesson=lesson_map[2],
                category=ForumPostCategory.SHARE,
                content="可以把数据看成教材，算法看成学习方法，算力看成学习速度。三者缺一不可，否则模型很难表现稳定。",
            )
            note_3 = self._ensure_post(
                title="学习笔记：AI 伦理讨论后的反思",
                author=student,
                lesson=lesson_map[3],
                category=ForumPostCategory.SHARE,
                content="AI 工具确实提高效率，但如果没有透明规则和责任边界，技术越强，风险也可能越大。",
            )
            note_4 = self._ensure_post(
                title="学习笔记：单元总结与未来期待",
                author=student,
                lesson=lesson_map[4],
                category=ForumPostCategory.SHARE,
                content="本单元最重要的收获是，不应只把 AI 当工具，更要理解它如何影响社会。未来最想继续探索的是生成式 AI 的创作边界。",
            )

            self._ensure_comment(post=discussion_1, author=teacher, content="推荐系统是非常好的例子，可以继续思考它依赖了哪些用户数据。")
            reply = self._ensure_comment(post=discussion_2, author=teacher, content="是的，数据量和数据多样性都会影响语音识别效果。")
            self._ensure_comment(post=discussion_2, author=student, content="明白了，噪声环境和口音差异也应该算在数据多样性里。", parent=reply)
            self._ensure_comment(post=discussion_3, author=admin, content="这也是课程答辩里很适合展开的一道思辨题。")
            self._ensure_comment(post=note_2, author=teacher, content="这个类比很清晰，适合作为课堂展示发言的开头。")

            for target_post in [discussion_1, discussion_2, discussion_3, note_2]:
                self._ensure_like(post=target_post, user=teacher)
            for target_post in [discussion_1, discussion_2, note_1, note_2, note_3]:
                self._ensure_like(post=target_post, user=student)
            for target_post in [discussion_1, discussion_3, note_4]:
                self._ensure_like(post=target_post, user=admin)

            self._ensure_progress(user=student, lesson=lesson_map[1], view_count=5, completed=True)
            self._ensure_progress(user=student, lesson=lesson_map[2], view_count=4, completed=True)
            self._ensure_progress(user=student, lesson=lesson_map[3], view_count=2, completed=False)
            self._ensure_progress(user=student, lesson=lesson_map[4], view_count=1, completed=False)
            QuizSubmission.objects.filter(user=student, lesson__in=[lesson_map[1], lesson_map[2]]).delete()
            WrongQuestion.objects.filter(user=student, question__lesson__in=[lesson_map[1], lesson_map[2], lesson_map[3]]).delete()

            submission_1 = QuizSubmission.objects.create(
                user=student,
                lesson=lesson_map[1],
                total_questions=5,
                correct_count=4,
                total_score=25,
                earned_score=20,
                accuracy=80,
            )
            for question in lesson_questions[1][:4]:
                QuizAnswer.objects.create(
                    submission=submission_1,
                    question=question,
                    user_answer=question.correct_answer,
                    expected_answer=question.correct_answer,
                    is_correct=True,
                    score_awarded=question.score,
                    explanation_snapshot=question.explanation,
                )
            wrong_question = lesson_questions[1][4]
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

            submission_2 = QuizSubmission.objects.create(
                user=student,
                lesson=lesson_map[2],
                total_questions=5,
                correct_count=5,
                total_score=25,
                earned_score=25,
                accuracy=100,
            )
            for question in lesson_questions[2]:
                QuizAnswer.objects.create(
                    submission=submission_2,
                    question=question,
                    user_answer=question.correct_answer,
                    expected_answer=question.correct_answer,
                    is_correct=True,
                    score_awarded=question.score,
                    explanation_snapshot=question.explanation,
                )

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

            guide_4 = TeachingGuide.objects.get(course=course, order_no=4)
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
                target_id=created_resources["AI 辩论素材包"].id,
                title_snapshot="AI 辩论素材包",
                url_snapshot=created_resources["AI 辩论素材包"].get_absolute_url(),
            )
            self._ensure_favorite(
                user=student,
                target_type=FavoriteTargetType.POST,
                target_id=discussion_3.id,
                title_snapshot=discussion_3.title,
                url_snapshot=reverse("forum:post_detail", kwargs={"post_id": discussion_3.id}),
            )
            self._ensure_favorite(
                user=student,
                target_type=FavoriteTargetType.GUIDE,
                target_id=guide_4.id,
                title_snapshot=guide_4.title,
                url_snapshot=guide_4.get_absolute_url(),
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
