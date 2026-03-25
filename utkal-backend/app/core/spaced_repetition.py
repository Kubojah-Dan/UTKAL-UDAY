"""
SM-2 Spaced Repetition Algorithm
Schedules question reviews for long-term retention.
quality: 0=blackout, 1=wrong, 2=wrong but familiar, 3=correct hard, 4=correct, 5=perfect
"""
from datetime import datetime, timedelta
from typing import Optional


def sm2_next_review(ease_factor: float, interval: int, quality: int):
    """
    Returns (new_interval_days, new_ease_factor)
    """
    if quality < 3:
        return 1, max(1.3, ease_factor - 0.2)
    if interval == 0:
        new_interval = 1
    elif interval == 1:
        new_interval = 6
    else:
        new_interval = round(interval * ease_factor)
    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    return new_interval, max(1.3, new_ef)


def outcome_to_quality(correct: bool, time_ms: int, hints: int) -> int:
    """Convert interaction outcome to SM-2 quality score 0-5"""
    if not correct:
        return 1 if hints > 0 else 0
    if time_ms < 10000 and hints == 0:
        return 5  # perfect
    if hints == 0:
        return 4  # correct, no hints
    return 3  # correct with hints


def get_next_review_date(correct: bool, time_ms: int, hints: int,
                          ease_factor: float = 2.5, interval: int = 0) -> dict:
    quality = outcome_to_quality(correct, time_ms, hints)
    new_interval, new_ef = sm2_next_review(ease_factor, interval, quality)
    next_date = datetime.utcnow() + timedelta(days=new_interval)
    return {
        "interval_days": new_interval,
        "ease_factor": round(new_ef, 3),
        "next_review": next_date.isoformat(),
        "quality": quality
    }
