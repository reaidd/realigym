"""UI strings for the recommender (EN / 繁中). Chinese is a draft → 🔍 zh-names."""
from __future__ import annotations

from .recommend import Reason

MESSAGES = {
    "fits_days": {
        "en": "Fits your schedule: {days} gym days a week (you have {available}).",
        "zh": "配合你的時間：每週 {days} 天健身（你有 {available} 天）。",
    },
    "level_match": {
        "en": "Designed for your experience level ({level}).",
        "zh": "專為你的程度（{level}）而設。",
    },
    "beginner_start_simple": {
        "en": "As a beginner, fewer sessions with more recovery gets you most of the gains. "
              "You can move up once you're hooked.",
        "zh": "初學者以較少訓練日、較多休息已可取得大部分進步，之後可再增加訓練日。",
    },
    "limited_variant": {
        "en": "Uses the limited-equipment version of this programme.",
        "zh": "採用此計劃的器材有限版本。",
    },
    "needs_more_days": {
        "en": "Every programme needs at least {days} days a week — this is the closest fit.",
        "zh": "所有計劃至少需要每週 {days} 天，這是最接近的選擇。",
    },
    "equipment_mismatch": {
        "en": "No programme has a version for your equipment yet; some exercises may need swapping.",
        "zh": "暫時沒有適合你器材的版本，部分動作可能需要替換。",
    },
    "session_too_long": {
        "en": "Sessions take about {estimate} min, more than your {available} min. "
              "Cutting isolation exercises to 2 sets brings it to about {trimmed} min.",
        "zh": "每次訓練約需 {estimate} 分鐘，超過你的 {available} 分鐘。"
              "將孤立動作減至 2 組可縮短至約 {trimmed} 分鐘。",
    },
    "health_check": {
        "en": "You mentioned an injury or health condition — please check with a doctor or "
              "physiotherapist before starting, especially before heavy lifts that involve holding your breath.",
        "zh": "你提及有傷患或健康狀況，開始前請先諮詢醫生或物理治療師，尤其是需要閉氣的大重量動作。",
    },
}


def render(reason: Reason, lang: str = "en") -> str:
    msg = MESSAGES[reason.code]
    return (msg.get(lang) or msg["en"]).format(**reason.params)
