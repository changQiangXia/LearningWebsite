from courses.models import ContentAuditLog


def log_content_action(
    *,
    actor,
    target_type,
    target_id,
    action,
    message,
    course=None,
    chapter=None,
    lesson=None,
    payload=None,
):
    """Persist a lightweight content operation log row."""
    return ContentAuditLog.objects.create(
        actor=actor,
        course=course,
        chapter=chapter,
        lesson=lesson,
        target_type=target_type,
        target_id=target_id,
        action=action,
        message=message,
        payload=payload or {},
    )
