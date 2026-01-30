# admin/eligibility_parser.py
import re

def parse_eligibility(text: str):
    """
    입력된 참가자격 문장에서 나이 조건을 정형화합니다.
    반환: (age_min, age_max, condition_type, keyword_hit)
    condition_type: range | min | max | keyword | none
    """
    if not text or not text.strip():
        return None, None, "none", None

    t = text.replace(" ", "")
    # 1) 범위: 19세~39세, 19~39세
    m = re.search(r"(\d{1,2})세?[~\-](\d{1,2})세?", t)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return min(a, b), max(a, b), "range", None

    # 2) 이상: 만19세이상, 19세이상, 19세부터
    m = re.search(r"(?:만)?(\d{1,2})세?(?:이상|부터)", t)
    if m:
        a = int(m.group(1))
        return a, None, "min", None

    # 3) 이하: 40세이하
    m = re.search(r"(\d{1,2})세?(?:이하|까지)", t)
    if m:
        b = int(m.group(1))
        return None, b, "max", None

    # 4) 키워드 기반(숫자 없음)
    keyword_map = {
        "청소년": ("keyword", "청소년"),
        "중학생": ("keyword", "중학생"),
        "고등학생": ("keyword", "고등학생"),
        "대학생": ("keyword", "대학생"),
        "대학원생": ("keyword", "대학원생"),
        "일반인": ("keyword", "일반인"),
        "누구나": ("keyword", "누구나"),
        "전국민": ("keyword", "전국민"),
    }
    for k, v in keyword_map.items():
        if k in t:
            return None, None, v[0], v[1]

    return None, None, "none", None
