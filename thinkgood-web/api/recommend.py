from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
from recommender import Recommender

app = FastAPI()

# CORS 설정 (모든 도메인에서 요청 가능하도록 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_NOW = pd.Timestamp("2023-02-11")

# --------------------------------------------------
# 코드 -> 한글 매핑 (Streamlit app.py와 동일)
# --------------------------------------------------
MANUAL_CODES = {
    "HORG001": "중앙정부/기관", "HORG002": "공기업", "HORG003": "대기업",
    "HORG004": "신문/방송/언론", "HORG005": "외국계기업", "HORG006": "지방자치단체",
    "HORG007": "학교/재단/협회", "HORG008": "중소/벤처기업", "HORG009": "학회/비영리단체",
    "HORG010": "해외", "HORG011": "대행사", "HORG012": "진흥원/공공기관",
    "CCFD001": "건축", "CCFD002": "게임/소프트웨어", "CCFD003": "과학",
    "CCFD004": "광고/마케팅", "CCFD005": "기획/아이디어", "CCFD006": "네이밍/슬로건",
    "CCFD007": "논문", "CCFD008": "대회", "CCFD009": "디자인",
    "CCFD010": "만화/캐릭터", "CCFD011": "문학/수기", "CCFD012": "미술",
    "CCFD013": "사진", "CCFD014": "영상/UCC", "CCFD015": "음악",
    "CCFD016": "이벤트", "CCFD017": "취업/창업", "CCFD018": "해외",
}
CODE_MAP = MANUAL_CODES.copy()

STRATEGY_INFO = {
    "GUEST": {
        "method": "Popularity (Logs + Hits)",
        "desc": "개인화 신호가 없는 사용자는 지원 로그 기반 인기와 조회수(Hit)를 결합해 지금 뜨는 공모전을 추천합니다.",
    },
    "DORMANT": {
        "method": "Popularity × Ease",
        "desc": "오랜만에 온 사용자는 인기 공모전 중에서도 진입장벽이 낮은 EASY 유형을 우선 노출합니다.",
    },
    "LIGHT": {
        "method": "Interest Matching + Popularity",
        "desc": "관심사(CCF_interests)와 공모전 분야를 매칭해 추천하며, 인기도를 보조 신호로 반영합니다.",
    },
    "POWER": {
        "method": "Hybrid (History + Interest + Popularity)",
        "desc": "과거 지원 이력과 관심사를 함께 사용해 개인화 매칭을 강화하고, 인기도를 소폭 반영합니다.",
    },
}

SEGMENT_DISPLAY = {
    "GUEST": "GUEST (비회원)",
    "DORMANT": "DORMANT (휴면 회원)",
    "LIGHT": "LIGHT (라이트 회원)",
    "POWER": "POWER (파워 회원)",
}

DEMO_ACCOUNTS = [
    {"label": "파워회원(1)", "user_id": "M22_02522", "expected_seg": "POWER"},
    {"label": "파워회원(2)", "user_id": "M15_01349", "expected_seg": "POWER"},
    {"label": "파워회원(3)", "user_id": "M22_07072", "expected_seg": "POWER"},
    {"label": "라이트회원(1)", "user_id": "M22_05203", "expected_seg": "LIGHT"},
    {"label": "라이트회원(2)", "user_id": "M21_01623", "expected_seg": "LIGHT"},
    {"label": "휴면회원", "user_id": "M10_00108", "expected_seg": "DORMANT"},
]

CATEGORIES = [
    "전체", "기획/아이디어", "광고/마케팅", "논문/리포트", "영상/UCC/사진",
    "디자인/캐릭터/웹툰", "IT/소프트웨어", "과학/공학", "문학/수기",
    "건축/인테리어", "취업/창업",
]

# --------------------------------------------------
# 데이터 로드
# --------------------------------------------------
recommender = None
contest_df = None
user_master = None
user_log = None
load_error = None

try:
    contest_df = pd.read_parquet(os.path.join(BASE_DIR, "Contest.parquet"))
    user_master = pd.read_parquet(os.path.join(BASE_DIR, "User_Master.parquet"))
    user_log = pd.read_parquet(os.path.join(BASE_DIR, "User_Activity_Log.parquet"))

    contest_df["contest_pk"] = contest_df["contest_pk"].astype(str)
    user_master["member_pk"] = user_master["member_pk"].astype(str)
    if "member_pk" in user_log.columns:
        user_log["member_pk"] = user_log["member_pk"].astype(str)
    if "contest_pk" in user_log.columns:
        user_log["contest_pk"] = user_log["contest_pk"].astype(str)
    if "putup_edt" in contest_df.columns:
        contest_df["putup_edt"] = pd.to_datetime(contest_df["putup_edt"], errors="coerce")

    try:
        map_df = pd.read_parquet(os.path.join(BASE_DIR, "wnc_category_detail_tb.parquet"))
        if "category_detail_cd" in map_df.columns and "category_detail_nm" in map_df.columns:
            keys, vals = map_df["category_detail_cd"], map_df["category_detail_nm"]
        elif len(map_df.columns) >= 5:
            keys, vals = map_df.iloc[:, 2], map_df.iloc[:, 4]
        else:
            keys, vals = map_df.iloc[:, 0], map_df.iloc[:, 1]
        k_clean = keys.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        v_clean = vals.astype(str).str.strip()
        CODE_MAP.update(dict(zip(k_clean, v_clean)))
    except Exception:
        pass  # 매핑 파일이 없어도 MANUAL_CODES로 동작

    recommender = Recommender(user_master, user_log, contest_df, now_ts=SIM_NOW)
except Exception as e:
    load_error = str(e)
    print(f"Data Load Error: {e}")


# --------------------------------------------------
# 유틸
# --------------------------------------------------
def get_mapped_name(code):
    if code is None or (isinstance(code, float) and pd.isna(code)):
        return "-"
    c = str(code).strip().replace(".0", "")
    return CODE_MAP.get(c, c)


def get_full_image_url(url):
    if url is None or (isinstance(url, float) and pd.isna(url)) or str(url).lower() == "nan":
        return None
    s = str(url).strip()
    if not s:
        return None
    if s.startswith("http"):
        return s
    if s.startswith("/"):
        return f"https://www.thinkcontest.com{s}"
    return s


def ensure_dday(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    if "putup_edt" in df.columns and "d_day" not in df.columns:
        df = df.copy()
        df["putup_edt"] = pd.to_datetime(df["putup_edt"], errors="coerce")
        df["d_day"] = (df["putup_edt"] - SIM_NOW).dt.days
    return df


def clean_records(df: pd.DataFrame):
    """DataFrame -> JSON-safe list[dict], 화면에 필요한 파생 필드 추가"""
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%d")
    df = df.replace({np.nan: None})
    records = df.to_dict(orient="records")

    for r in records:
        raw_host = r.get("organ_nm") or r.get("host_company") or r.get("host_organ")
        r["host_display"] = get_mapped_name(raw_host) if raw_host else "-"
        r["img_url_full"] = get_full_image_url(r.get("img_url"))
        if r.get("d_day") is not None:
            try:
                r["d_day"] = int(r["d_day"])
            except (TypeError, ValueError):
                pass
    return records


def build_profile(user_id: str):
    if user_master is None:
        return None
    if str(user_id) not in user_master["member_pk"].astype(str).values:
        return None

    u = user_master[user_master["member_pk"].astype(str) == str(user_id)].iloc[0]
    interests_raw = str(u.get("CCF_interests", "") or "")
    codes = [c.strip() for c in interests_raw.split(",") if c.strip()]
    interest_txt = ", ".join([get_mapped_name(c) for c in codes]) if codes else "-"
    apply_cnt = int(u.get("n_apply", 0) or 0)
    apply_info_txt = "지원 이력 없음"

    if apply_cnt > 0 and user_log is not None and not user_log.empty:
        user_logs = user_log[user_log["member_pk"].astype(str) == str(user_id)]
        applied_pks = user_logs["contest_pk"].astype(str).unique()
        applied = contest_df[contest_df["contest_pk"].astype(str).isin(applied_pks)]

        if not applied.empty and "분야_한글" in applied.columns:
            fields = []
            for f in applied["분야_한글"].dropna():
                fields.extend([x.strip() for x in str(f).split(",") if x.strip()])
            if fields:
                counts = Counter(fields).most_common(3)
                apply_info_txt = ", ".join([f"{k}({v})" for k, v in counts])
            else:
                apply_info_txt = f"총 {apply_cnt}회 지원"
        else:
            apply_info_txt = f"총 {apply_cnt}회 지원"

    return {
        "interest_txt": interest_txt,
        "apply_cnt": apply_cnt,
        "apply_info_txt": apply_info_txt,
    }


# --------------------------------------------------
# 엔드포인트
# --------------------------------------------------
@app.get("/api/recommend")
def get_recommendation(user_id: str = Query(...), top_n: int = Query(12)):
    if recommender is None:
        return {"error": f"엔진이 로드되지 않았습니다. ({load_error})"}

    recs, segment, reason = recommender.get_recommendations(user_id, top_n=top_n)
    recs = ensure_dday(recs) if recs is not None else recs
    recommendations = clean_records(recs) if recs is not None and not recs.empty else []

    return {
        "user_id": user_id,
        "segment": segment,
        "segment_display": SEGMENT_DISPLAY.get(segment, segment),
        "reason": reason,
        "strategy": STRATEGY_INFO.get(segment, STRATEGY_INFO["GUEST"]),
        "profile": build_profile(user_id),
        "recommendations": recommendations,
    }


@app.get("/api/meta")
def get_meta():
    """프론트에서 데모 계정/카테고리 목록을 하드코딩하지 않도록 제공"""
    return {
        "demo_accounts": DEMO_ACCOUNTS,
        "categories": CATEGORIES,
    }
