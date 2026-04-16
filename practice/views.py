from io import BytesIO

from PIL import Image, ImageStat

from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse

from courses.ai_unit_data import LESSON_PAGE_DATA
from courses.models import CourseStatus, LearningProgress, Lesson
from quiz.models import Question, QuizSubmission

from .forms import DialogueForm, ImageRecognitionForm, SpeechTranscriptForm
from .models import PracticeRecord, PracticeRecordType
from .services import QwenServiceError, analyze_image_with_qwen, generate_ai_dialogue_reply, qwen_is_enabled


def _dialogue_reply(message: str) -> str:
    content = (message or "").strip()
    lower = content.lower()
    if not content:
        return "可以先提出一个和人工智能课程相关的问题，例如“什么是人工智能”或“AI 为什么需要数据”。"
    if "课程" in content or "course" in lower:
        return "设计一门人工智能入门课程时，可以先明确学习目标，再安排概念、应用、伦理和总结四个学习阶段。"
    if "答辩" in content or "defense" in lower:
        return "答辩展示可按项目背景、核心功能、技术实现、测试结果和演示流程五个部分来组织。"
    if "资源" in content or "search" in lower:
        return "资源整理时建议统一标签、课时归属和资源类型，这样更便于检索、推荐和课堂使用。"
    if "ai" in lower or "人工智能" in content:
        return "人工智能可以理解为让机器模拟人的感知、学习、判断与决策能力，常见应用包括语音识别、图像识别和智能对话。"
    return "当前问题可以继续细化一些，例如直接询问人工智能的概念、应用场景、伦理问题或未来发展趋势。"


def _analyze_image(image_bytes: bytes):
    image = Image.open(BytesIO(image_bytes))
    grayscale = image.convert("L")
    avg_brightness = round(ImageStat.Stat(grayscale).mean[0], 2)
    width, height = image.size
    orientation = "横向" if width > height else "纵向" if height > width else "方形"

    labels = []
    if image.format:
        labels.append(f"图片格式：{image.format}")
    labels.append(f"图片尺寸：{width} x {height}")
    labels.append(f"版式方向：{orientation}")
    labels.append(f"平均亮度：{avg_brightness}")

    if image.format == "PNG" and avg_brightness >= 170:
        labels.append("基础判断：可能是界面截图或浅色背景图片。")
    elif image.format in {"JPEG", "JPG"}:
        labels.append("基础判断：更接近照片类图片。")
    elif avg_brightness < 85:
        labels.append("基础判断：画面整体偏暗。")
    else:
        labels.append("基础判断：画面亮度和版式较为常规。")

    return {
        "format": image.format or "未知",
        "width": width,
        "height": height,
        "orientation": orientation,
        "brightness": avg_brightness,
        "labels": labels,
    }


def _build_saved_output_text(analysis: dict, ai_result: str | None = None) -> str:
    local_result = "；".join(analysis["labels"])
    if ai_result:
        return f"{local_result}；AI识别结果：{ai_result}"
    return local_result


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
            "icon": "🎙️",
            "title": "语音识别体验",
            "subtitle": "感受 AI「听觉感知能力」",
            "description": "对着麦克风说话，AI 将语音自动转成文字，看看它能不能听懂。",
            "lesson": "对应课时：第一课时 · 认识人工智能",
            "button_label": "开始体验",
            "url": reverse("practice:speech_lab"),
        },
        {
            "icon": "💬",
            "title": "AI 智能对话体验",
            "subtitle": "感受 AI「语言理解与学习能力」",
            "description": "和 AI 自由聊天，提问人工智能概念、应用、伦理或未来趋势。",
            "lesson": "对应课时：第二课时 · 人工智能如何工作",
            "button_label": "进入对话",
            "url": reverse("practice:dialogue_lab"),
        },
        {
            "icon": "📷",
            "title": "图像识别体验",
            "subtitle": "感受 AI「视觉感知能力」",
            "description": "上传一张图片，让 AI 看看图里有什么，并给出简洁的识别结论。",
            "lesson": "对应课时：第一课时 · 认识人工智能",
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
            "qwen_enabled": qwen_is_enabled(),
        },
    )


def dialogue_lab(request):
    history = request.session.get("dialogue_history", [])
    reply = None
    provider_label = "本地兜底"

    if request.method == "POST":
        form = DialogueForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data["message"]
            try:
                if qwen_is_enabled():
                    reply = generate_ai_dialogue_reply(message)
                    provider_label = "Qwen"
                else:
                    reply = _dialogue_reply(message)
            except QwenServiceError as exc:
                messages.warning(request, f"{exc} 已自动切换为本地演示回复。")
                reply = _dialogue_reply(message)

            history.append({"question": message, "answer": reply, "provider": provider_label})
            history = history[-8:]
            request.session["dialogue_history"] = history
            if request.user.is_authenticated:
                PracticeRecord.objects.create(
                    user=request.user,
                    practice_type=PracticeRecordType.DIALOGUE,
                    input_text=message,
                    output_text=reply,
                    metadata={"provider": provider_label},
                )
    else:
        form = DialogueForm()

    return render(
        request,
        "practice/dialogue_lab.html",
        {
            "form": form,
            "history": history,
            "reply": reply,
            "provider_label": provider_label,
            "qwen_enabled": qwen_is_enabled(),
        },
    )


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
                    output_text="已保存语音识别文本。",
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
            image_bytes = image_file.read()
            analysis = _analyze_image(image_bytes)
            analysis["provider"] = "本地分析"
            analysis["ai_result"] = None

            try:
                if qwen_is_enabled():
                    analysis["ai_result"] = analyze_image_with_qwen(
                        image_name=image_file.name,
                        image_bytes=image_bytes,
                        content_type=getattr(image_file, "content_type", None),
                    )
                    analysis["provider"] = "Qwen + 本地分析"
            except QwenServiceError as exc:
                messages.warning(request, f"{exc} 当前先展示本地分析结果。")

            if request.user.is_authenticated:
                PracticeRecord.objects.create(
                    user=request.user,
                    practice_type=PracticeRecordType.IMAGE,
                    output_text=_build_saved_output_text(analysis, analysis.get("ai_result")),
                    image=image_file,
                    metadata=analysis,
                )
    else:
        form = ImageRecognitionForm()

    return render(
        request,
        "practice/image_lab.html",
        {
            "form": form,
            "analysis": analysis,
            "qwen_enabled": qwen_is_enabled(),
        },
    )
