# admin/keyword_extractor.py
import re
from collections import Counter

# 아주 간단한 한국어/영어 스톱워드(데모용)
STOPWORDS = set([
    "및","등","수","것","이","가","을","를","은","는","에","의","와","과","로","으로",
    "대상","참여","가능","제출","방법","일정","문의","관련","사항","안내","선정","지원",
    "the","and","or","to","in","for","on","with","a","an"
])

def extract_keywords(text: str, top_k: int = 8):
    if not text:
        return []

    # 한글/영문/숫자만 남기고 토큰화
    tokens = re.findall(r"[가-힣A-Za-z0-9]{2,}", text)
    tokens = [t.lower() for t in tokens if t.lower() not in STOPWORDS]

    if not tokens:
        return []
    counts = Counter(tokens)
    return [w for w, _ in counts.most_common(top_k)]
