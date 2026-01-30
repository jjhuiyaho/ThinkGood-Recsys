# admin/schema.py
from datetime import datetime

def build_record(payload: dict) -> dict:
    """
    화면 입력값(payload)을 '정형 레코드'로 변환합니다.
    데모용이라 엄격한 검증은 최소만 합니다.
    """
    rec = dict(payload)
    rec["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 날짜는 문자열로 저장(YYYY-MM-DD). Streamlit date_input은 date 객체 -> str 변환 권장
    for k in ["apply_start_date", "apply_end_date", "extended_end_date"]:
        v = rec.get(k)
        rec[k] = v.isoformat() if hasattr(v, "isoformat") and v else None

    return rec
