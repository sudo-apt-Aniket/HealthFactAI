from datetime import datetime, date, timedelta
from typing import Optional, Tuple


def dates_equal(d1: date, d2: date) -> bool:
    return d1.year == d2.year and d1.month == d2.month and d1.day == d2.day


def parse_last_activity(raw: Optional[str]) -> Optional[date]:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None


def compute_new_streak(
    current_streak: Optional[int],
    longest_streak: Optional[int],
    last_activity_raw: Optional[str],
    today: Optional[date] = None,
) -> Tuple[int, int, str]:
    """Return (new_current, new_longest, new_last_activity_str)."""
    today = today or date.today()
    yesterday = today - timedelta(days=1)

    current_streak = current_streak or 0
    longest_streak = longest_streak or 0

    last_activity = parse_last_activity(last_activity_raw)

    if last_activity is None:
        new_current = 1
    else:
        if dates_equal(last_activity, today):
            new_current = current_streak or 1
        elif dates_equal(last_activity, yesterday):
            new_current = current_streak + 1
        else:
            new_current = 1

    new_longest = max(longest_streak, new_current)
    return new_current, new_longest, today.strftime("%Y-%m-%d")


