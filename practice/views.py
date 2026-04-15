from PIL import Image, ImageStat

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import render

from courses.ai_unit_data import LESSON_PAGE_DATA
from courses.models import CourseStatus, LearningProgress, Lesson
from quiz.models import Question, QuizSubmission

from .forms import DialogueForm, ImageRecognitionForm, SpeechTranscriptForm
from .models import PracticeRecord, PracticeRecordType


def _dialogue_reply(message: str):
    content = (message or "").strip()
    lower = content.lower()
    if not content:
        return "可以先提出一个和 AI 学习、课程规划或答题训练相关的问题。"
    if "课程" in content or "course" in lower:
        return "建议从教学目标、核心知识点、练习任务和评价方式四个层面来设计课程结构。"
    if "答辩" in content or "defense" in lower:
        return "答辩展示可以按照系统背景、功能模块、技术方案、测试结果和演示流程来组织。"
    if "搜索" in content or "resource" in lower:
        return "资源整合时建议统一标签、类型和关联课程，便于后续检索与推荐。"
    if "ai" in lower or "人工智能" in content:
        return "AI 应用展示可以从语音识别、图像识别、智能问答和学习分析四个方向展开。"
    return "当前对话引擎采用规则增强方式，可继续追问课程设计、学习路径、资源整理或答辩展示。"


def _analyze_image(image_file):
    image = Image.open(image_file)
    grayscale = image.convert("L")
    avg_brightness = round(ImageStat.Stat(grayscale).mean[0], 2)
    width, height = image.size
    orientation = "横向" if width > height else "纵向" if height > width else "方形"

    labels = []
    if image.format:
        labels.append(f"格式：{image.format}")
    labels.append(f"尺寸：{width} x {height}")
    labels.append(f"版式：{orientation}")
    labels.append(f"平均亮度：{avg_brightness}")

    if image.format == "PNG" and avg_brightness >= 170:
        labels.append("推测类型：浅色界面截图")
    elif image.format in {"JPEG", "JPG"}:
        labels.append("推测类型：照片素材")
    elif avg_brightness < 85:
        labels.append("画面特征：偏暗")
    else:
        labels.append("画面特征：普通图像")

    return {
        "format": image.format or "未知",
        "width": width,
        "height": height,
        "orientation": orientation,
        "brightness": avg_brightness,
        "labels": labels,
    }


def index(request):
    lessons = list(
        Lesson.objects.filter(
            is_active=True,
            chapter__is_active=True,
            chapter__course__status=CourseStatus.PUBLISHED,
        )
        .select_related("chapter", "chapter__course")
        .order_by("chapter__course_id", "chapter__order_no", "order_no", "id")[:4]
    )

    lesson_ids = [lesson.id for lesson in lessons]
    progress_map = {}
    latest_submission_map = {}
    question_count_map = {
        lesson.id: Question.objects.filter(lesson=lesson, is_active=True).count()
        for lesson in lessons
    }

    if request.user.is_authenticated and lesson_ids:
        progress_map = {
            progress.lesson_id: progress
            for progress in LearningProgress.objects.filter(user=request.user, lesson_id__in=lesson_ids)
        }
        for submission in (
            QuizSubmission.objects.filter(user=request.user, lesson_id__in=lesson_ids)
            .select_related("lesson")
            .order_by("lesson_id", "-submitted_at", "-id")
        ):
            latest_submission_map.setdefault(submission.lesson_id, submission)

    lesson_cards = []
    for lesson in lessons:
        lesson_meta = LESSON_PAGE_DATA.get(lesson.order_no, {})
        progress = progress_map.get(lesson.id)
        submission = latest_submission_map.get(lesson.id)
        if submission:
            percent = 100
            status_label = "已完成"
            action_label = f"查看成绩（{submission.accuracy}%）"
            action_url = reverse("quiz:submission_history")
        elif progress and (progress.completed or progress.view_count > 0):
            percent = 50
            status_label = "进行中"
            action_label = "开始测试"
            action_url = reverse("quiz:take_lesson_quiz", kwargs={"lesson_id": lesson.id})
        else:
            percent = 0
            status_label = "未开始"
            action_label = "开始测试"
            action_url = reverse("quiz:take_lesson_quiz", kwargs={"lesson_id": lesson.id})

        lesson_cards.append(
            {
                "lesson": lesson,
                "summary": lesson_meta.get("hero_summary", lesson.content),
                "progress_percent": percent,
                "status_label": status_label,
                "question_total": question_count_map.get(lesson.id, 0),
                "action_label": action_label,
                "action_url": action_url,
            }
        )

    labs = [
        {
            "icon": "🎤",
            "title": "语音识别体验",
            "subtitle": "感受 AI「听觉感知能力」",
            "description": "对着麦克风说话，AI 将语音自动转成文字，看看它能不能听懂你。",
            "lesson": "第一课时 · 认识人工智能",
            "button_label": "开始体验",
            "url": reverse("practice:speech_lab"),
        },
        {
            "icon": "💬",
            "title": "AI 智能对话体验",
            "subtitle": "感受 AI「语言理解&学习能力」",
            "description": "和 AI 自由聊天，问问它：你靠什么才能学会回答问题？",
            "lesson": "第二课时 · 人工智能如何工作",
            "button_label": "进入对话",
            "url": reverse("practice:dialogue_lab"),
        },
        {
            "icon": "📷",
            "title": "图像识别体验",
            "subtitle": "感受 AI「视觉感知能力」",
            "description": "上传一张图片，让 AI 看看图里有什么，体验它的视觉识别能力。",
            "lesson": "第一课时 · 认识人工智能",
            "button_label": "上传识别",
            "url": reverse("practice:image_lab"),
        },
    ]

    return render(
        request,
        "practice/index.html",
        {
            "labs": labs,
            "lesson_cards": lesson_cards,
        },
    )


def dialogue_lab(request):
    history = request.session.get("dialogue_history", [])
    reply = None
    if request.method == "POST":
        form = DialogueForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data["message"]
            reply = _dialogue_reply(message)
            history.append({"question": message, "answer": reply})
            history = history[-8:]
            request.session["dialogue_history"] = history
            if request.user.is_authenticated:
                PracticeRecord.objects.create(
                    user=request.user,
                    practice_type=PracticeRecordType.DIALOGUE,
                    input_text=message,
                    output_text=reply,
                )
    else:
        form = DialogueForm()
    return render(request, "practice/dialogue_lab.html", {"form": form, "history": history, "reply": reply})


def speech_lab(request):
    saved_transcript = None
    if request.method == "POST":
        form = SpeechTranscriptForm(request.POST)
        if form.is_valid():
            saved_transcript = form.cleaned_data["transcript"]
            if request.user.is_authenticated and saved_transcript:
                PracticeRecord.objects.create(
                    user=request.user,
                    practice_type=PracticeRecordType.SPEECH,
                    input_text=saved_transcript,
                    output_text="已保存识别文本。",
                )
            messages.success(request, "语音识别文本已记录。")
    else:
        form = SpeechTranscriptForm()
    return render(
        request,
        "practice/speech_lab.html",
        {"form": form, "saved_transcript": saved_transcript},
    )


def image_lab(request):
    analysis = None
    if request.method == "POST":
        form = ImageRecognitionForm(request.POST, request.FILES)
        if form.is_valid():
            image_file = form.cleaned_data["image"]
            analysis = _analyze_image(image_file)
            if request.user.is_authenticated:
                image_file.seek(0)
                PracticeRecord.objects.create(
                    user=request.user,
                    practice_type=PracticeRecordType.IMAGE,
                    output_text="；".join(analysis["labels"]),
                    image=image_file,
                    metadata=analysis,
                )
    else:
        form = ImageRecognitionForm()
    return render(request, "practice/image_lab.html", {"form": form, "analysis": analysis})

# Create your views here.
