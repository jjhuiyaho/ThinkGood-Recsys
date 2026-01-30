# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from collections import Counter
from recommender import Recommender

# --------------------------------------------------
# [설정] 기준일 (2023-02-11 시뮬레이션)
# --------------------------------------------------
SIM_NOW = pd.Timestamp("2023-02-11")

# --------------------------------------------------
# 페이지 설정 & CSS
# --------------------------------------------------
st.set_page_config(page_title="씽굿 큐레이션", layout="wide")

st.markdown(
    """<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; color: #333; background-color: #F8F9FA; }
    .stApp { background-color: #F8F9FA; }

    /* 로그인 화면 */
    .login-container { background-color: #FFFFFF; padding: 60px 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); text-align: center; margin-top: 40px; margin-bottom: 40px; border: 1px solid #EAEAEA; }
    .login-title { font-size: 2.0rem; font-weight: 800; color: #222; margin-bottom: 15px; letter-spacing: -0.5px; }
    .login-subtitle { font-size: 1.0rem; color: #666; margin-bottom: 40px; font-weight: 500; }

    /* 버튼 스타일 */
    div.stButton > button { width: 100%; border-radius: 6px; font-weight: 700; padding: 0.5rem 1rem; background-color: #D32F2F !important; color: white !important; border: none !important; }
    div.stButton > button:hover { background-color: #B71C1C !important; }
    button[kind="secondary"] { background-color: #555 !important; color: white !important; border: none !important; }

    /* 카드 스타일 */
    .card-container { background: #FFFFFF; border: 1px solid #EDEDED; border-radius: 12px; overflow: hidden; height: 350px; position: relative; transition: all 0.3s ease; box-shadow: 0 2px 8px rgba(0,0,0,0.03); display: flex; flex-direction: column; }
    .card-container:hover { border-color: #D32F2F; transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.08); }
    .card-img-wrapper { height: 150px; overflow: hidden; background: #F8F9FA; display: flex; align-items: center; justify-content: center; border-bottom: 1px solid #F1F1F1; flex-shrink: 0; }
    .card-img { width: 100%; height: 100%; object-fit: cover; }
    .card-content { padding: 16px; flex-grow: 1; display: flex; flex-direction: column; }

    .badge-dday { font-size: 0.75rem; color: #FFF; background: #D32F2F; padding: 3px 6px; border-radius: 4px; font-weight: 700; margin-right: 4px; vertical-align: middle; }
    .badge-cate { font-size: 0.75rem; color: #555; background: #F1F3F5; padding: 3px 6px; border-radius: 4px; vertical-align: middle; margin-right: 2px;}
    .badge-plus { font-size: 0.7rem; color: #888; border: 1px solid #DDD; padding: 2px 5px; border-radius: 4px; vertical-align: middle; }

    .card-title { font-size: 1rem; font-weight: 700; color: #222; margin-top: 10px; margin-bottom: 8px; height: 2.8em; overflow: hidden; line-height: 1.4; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
    .user-reason { font-size: 0.8rem; color: #D32F2F; font-weight: 700; margin-top: auto; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

    /* 프로필 박스 */
    .profile-box { background:#FFF; padding:15px; border-radius:8px; border:1px solid #E0E0E0; }
    .profile-row { display: flex; margin-top: 5px; font-size: 0.9rem; }
    .profile-label { width: 70px; font-weight: bold; color: #555; }
    .profile-val { flex: 1; color: #333; }

    /* 카드 미리보기 바 */
    .preview-bar { background-color: #263238; padding: 6px 14px; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #37474F; flex-shrink: 0; height: 36px; }
    .preview-label { color: #B0BEC5; font-size: 0.75rem; font-weight: 700; }
    .preview-score { color: #FF5252; font-weight: 900; font-size: 0.9rem; }

    /* 상세 모달: AI 요약 박스 */
    .summary-box {
        background-color: #E3F2FD;
        border-left: 5px solid #1565C0; /* 왼쪽 강조선 추가 */
        border-radius: 4px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .summary-badge {
        background-color: #1565C0;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 8px;
    }
    .summary-text {
        color: #0D47A1;
        font-size: 0.9rem;
        line-height: 1.6;
        font-weight: 500;
    }

    /* 상세 모달: 리포트 스타일 */
    .report-box { background:#263238; color:#fff; padding:16px; border-radius:8px; border:1px solid rgba(255,255,255,0.08); margin-top: 10px; }
    .report-title { font-weight:900; font-size:0.95rem; margin-bottom:12px; color: #ECEFF1; }
    .report-row { display:flex; align-items:center; justify-content:space-between; gap:12px; margin:10px 0; }
    .report-label { width:90px; color:#CFD8DC; font-size:0.85rem; font-weight:700; white-space:nowrap; }
    .report-bar-wrap { flex:1; height:8px; background:#37474F; border-radius:999px; overflow:hidden; }
    .report-bar { height:100%; background:#FF5252; border-radius:999px; }
    .report-val { width:30px; text-align:right; font-weight:900; color:#FFCDD2; font-size:0.85rem; }
    .report-desc { margin-top:12px; color:#B0BEC5; font-size:0.85rem; line-height:1.4; border-top: 1px solid #455A64; padding-top: 10px; }
    .report-total { margin-top:10px; display:flex; justify-content:flex-end; align-items:baseline; gap:8px; }
    .report-total-label { color:#B0BEC5; font-size:0.85rem; font-weight:700; }
    .report-total-score { color:#FF5252; font-size:1.2rem; font-weight:900; }

    /* 상세 페이지 테이블 스타일 */
    .spec-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.95rem;
        margin-bottom: 20px;
    }
    .spec-table td {
        padding: 10px 4px;
        border-bottom: 1px solid #EEEEEE;
        vertical-align: top; /* 텍스트 상단 정렬 */
    }
    .spec-label {
        width: 90px;
        font-weight: 700;
        color: #555;
        background-color: #F9F9F9;
        padding-left: 8px !important;
        border-radius: 4px 0 0 4px;
    }
    .spec-value {
        color: #333;
        padding-left: 12px !important;
        font-weight: 500;
    }
    .title-area {
        margin-bottom: 20px;
        border-bottom: 2px solid #333;
        padding-bottom: 15px;
    }
    .main-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: #111;
        margin-bottom: 8px;
        line-height: 1.3;
    }
    .sub-info {
        font-size: 0.85rem;
        color: #888;
        display: flex;
        gap: 12px;
    }

</style>""",
    unsafe_allow_html=True,
)

# --------------------------------------------------
# 데이터 로드
# --------------------------------------------------
@st.cache_data
def load_data_safe():
    try:
        contest = pd.read_parquet("Contest.parquet")
        user_master = pd.read_parquet("User_Master.parquet")
        user_log = pd.read_parquet("User_Activity_Log.parquet")
        mapping = pd.read_parquet("wnc_category_detail_tb.parquet")
    except Exception as e:
        st.error(f"데이터 로딩 실패: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    if "contest_pk" in contest.columns:
        contest["contest_pk"] = contest["contest_pk"].astype(str)
    if "member_pk" in user_master.columns:
        user_master["member_pk"] = user_master["member_pk"].astype(str)
    if "member_pk" in user_log.columns:
        user_log["member_pk"] = user_log["member_pk"].astype(str)
    if "contest_pk" in user_log.columns:
        user_log["contest_pk"] = user_log["contest_pk"].astype(str)

    for col, default in [("days_since_login", 0), ("n_apply", 0), ("login_cnt", 0), ("CCF_interests", "")]:
        if col not in user_master.columns:
            user_master[col] = default

    user_master["n_apply"] = pd.to_numeric(user_master["n_apply"], errors="coerce").fillna(0).astype(int)
    user_master["login_cnt"] = pd.to_numeric(user_master["login_cnt"], errors="coerce").fillna(0).astype(int)

    if "putup_edt" in contest.columns:
        contest["putup_edt"] = pd.to_datetime(contest["putup_edt"], errors="coerce")

    return contest, user_log, user_master, mapping


contest_df, User_Activity_log, User_Master, map_df = load_data_safe()

# --------------------------------------------------
# 코드 → 한글 매핑 (파일 + 비상용 하드코딩)
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
    "CCFD016": "이벤트", "CCFD017": "취업/창업", "CCFD018": "해외"
}

CODE_MAP = MANUAL_CODES.copy()

if map_df is not None and not map_df.empty:
    if "category_detail_cd" in map_df.columns and "category_detail_nm" in map_df.columns:
        keys = map_df["category_detail_cd"]
        vals = map_df["category_detail_nm"]
    elif len(map_df.columns) >= 5:
        keys = map_df.iloc[:, 2]  # category_detail_cd
        vals = map_df.iloc[:, 4]  # category_detail_nm
    else:
        keys = map_df.iloc[:, 0]
        vals = map_df.iloc[:, 1]
    
    try:
        k_clean = keys.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        v_clean = vals.astype(str).str.strip()
        CODE_MAP.update(dict(zip(k_clean, v_clean)))
    except Exception as e:
        pass


def get_mapped_name(code):
    if pd.isna(code):
        return "-"
    c = str(code).strip().replace(".0", "") 
    return CODE_MAP.get(c, c)


def codes_to_korean(codes_str) -> str:
    if codes_str is None:
        return "-"
    s = str(codes_str).strip()
    if not s or s.lower() == "nan":
        return "-"
    codes = [c.strip() for c in s.split(",") if c.strip()]
    if not codes:
        return "-"
    return ", ".join([get_mapped_name(c) for c in codes])


# --------------------------------------------------
# 추천 엔진
# --------------------------------------------------
@st.cache_resource
def get_engine(user_master, user_log, contest_df):
    if contest_df is None or contest_df.empty:
        return None
    return Recommender(user_master, user_log, contest_df, now_ts=SIM_NOW)


recommender = get_engine(User_Master, User_Activity_log, contest_df)

# --------------------------------------------------
# 세션 상태
# --------------------------------------------------
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "debug_mode" not in st.session_state:
    st.session_state["debug_mode"] = False
if "demo_expected_seg" not in st.session_state:
    st.session_state["demo_expected_seg"] = None
if "cached_recs" not in st.session_state:
    st.session_state["cached_recs"] = None
if "cached_uid" not in st.session_state:
    st.session_state["cached_uid"] = None

# --------------------------------------------------
# 텍스트/전략 정보
# --------------------------------------------------
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
CATEGORIES = [
    "전체",
    "기획/아이디어",
    "광고/마케팅",
    "논문/리포트",
    "영상/UCC/사진",
    "디자인/캐릭터/웹툰",
    "IT/소프트웨어",
    "과학/공학",
    "문학/수기",
    "건축/인테리어",
    "취업/창업",
]
DEMO_ACCOUNTS = [
    ("파워회원(1)", "M22_02522", "POWER"),
    ("파워회원(2)", "M15_01349", "POWER"),
    ("파워회원(3)", "M22_07072", "POWER"),
    ("라이트회원(1)", "M22_05203", "LIGHT"),
    ("라이트회원(2)", "M21_01623", "LIGHT"),
    ("휴면회원", "M10_00108", "DORMANT"),
]
SEGMENT_DISPLAY = {
    "GUEST": "GUEST (비회원)",
    "DORMANT": "DORMANT (휴면 회원)",
    "LIGHT": "LIGHT (라이트 회원)",
    "POWER": "POWER (파워 회원)",
}

# --------------------------------------------------
# 유틸
# --------------------------------------------------
def get_full_image_url(url):
    if pd.isna(url) or str(url) == "nan":
        return None
    url_str = str(url).strip()
    if not url_str:
        return None
    if url_str.startswith("http"):
        return url_str
    if url_str.startswith("/"):
        return f"https://www.thinkcontest.com{url_str}"
    return url_str


def ensure_dday(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    if "putup_edt" in df.columns and "d_day" not in df.columns:
        _today = SIM_NOW
        df = df.copy()
        df["d_day"] = (pd.to_datetime(df["putup_edt"], errors="coerce") - _today).dt.days
    return df


def safe_int100(x):
    try:
        x = float(x)
    except:
        x = 0.0
    x = max(0.0, min(100.0, x))
    return int(round(x))


def clamp01(x):
    try:
        x = float(x)
    except:
        x = 0.0
    return max(0.0, min(1.0, x))


def to100_from01(x):
    return int(round(clamp01(x) * 100))


def urgency_from_dday(d):
    try:
        d = float(d)
    except:
        return 0
    if d <= 0:
        return 100
    if d >= 30:
        return 0
    return int(round((1 - d / 30) * 100))


def calc_dday_from_row(row):
    if "d_day" in row and pd.notna(row.get("d_day")):
        try:
            return int(row.get("d_day"))
        except:
            return 999
    try:
        _today = SIM_NOW
        d = (pd.to_datetime(row.get("putup_edt"), errors="coerce") - _today).days
        return int(d) if pd.notna(d) else 999
    except:
        return 999


# --------------------------------------------------
# 리포트 렌더링
# --------------------------------------------------
def build_report_items(row):
    seg = str(row.get("user_segment", "GUEST")).strip()
    d_day = calc_dday_from_row(row)
    total = safe_int100(row.get("final_score", row.get("total_score", 0)))

    if seg == "POWER":
        h = to100_from01(row.get("norm_history", 0))
        i = to100_from01(row.get("norm_interest", 0))
        p = to100_from01(row.get("norm_pop", 0))
        items = [("이력 유사", h), ("관심 일치", i), ("인기", p)]
        desc = "과거 이력과 관심사를 기반으로 추천했습니다."
        return items, total, desc, seg

    if seg == "LIGHT":
        i = to100_from01(row.get("norm_interest", 0))
        p = to100_from01(row.get("norm_pop", 0))
        items = [("관심 일치", i), ("인기", p)]
        desc = "관심사와 유사한 공모전을 우선 노출했습니다."
        return items, total, desc, seg

    if seg == "DORMANT":
        p = to100_from01(row.get("norm_pop", 0))
        diff = row.get("diff_score", 1.0)
        try:
            diff = float(diff)
        except:
            diff = 1.0
        ease = 100 if diff >= 1.5 else 60
        items = [("입문 난이도", ease), ("인기", p)]
        desc = "부담 없이 시작하기 좋은 EASY 유형입니다."
        return items, total, desc, seg

    pop = to100_from01(row.get("norm_log", row.get("norm_pop", 0)))
    urg = urgency_from_dday(d_day)
    items = [("실시간 인기", pop), ("마감 임박", urg)]
    desc = "최근 사용자들이 많이 찾는 인기 공모전입니다."
    return items, total, desc, "GUEST"


# --------------------------------------------------
# 리포트 박스 렌더링 함수
# --------------------------------------------------
def render_report_box(row):
    items, total_s, desc_txt, seg = build_report_items(row)
    report_rows_html = ""
    for label, val in items[:3]:
        val = int(max(0, min(100, int(val))))
        report_rows_html += f"""
        <div class="report-row">
          <div class="report-label">{label}</div>
          <div class="report-bar-wrap"><div class="report-bar" style="width:{val}%;"></div></div>
          <div class="report-val">{val}</div>
        </div>
        """
    
    st.markdown(
        f"""
        <div class="report-box" style="margin-top:0;">
          <div class="report-title">AI 적합도 리포트</div>
          {report_rows_html}
          <div class="report-desc">{desc_txt}</div>
          <div class="report-total">
            <div class="report-total-label">종합 점수</div>
            <div class="report-total-score">{int(total_s)}점</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# 카드 / 상세 UI
# --------------------------------------------------
def render_card(row, key):
    d = row.get("d_day")
    if pd.isna(d) or d == "":
        d = 999
    try:
        d = int(d)
    except:
        d = 999

    if d >= 0:
        d_badge = f'<span class="badge-dday">D-{d}</span>'
    else:
        d_badge = f'<span class="badge-dday" style="background:#666">D+{abs(d)}</span>'

    raw_cats = str(row.get("분야_한글", ""))
    cats = [c.strip() for c in raw_cats.split(",") if c.strip()]

    if len(cats) > 1:
        c_badges = f'<span class="badge-cate">{cats[0]}</span><span class="badge-plus">+{len(cats)-1}</span>'
    elif len(cats) == 1:
        c_badges = f'<span class="badge-cate">{cats[0]}</span>'
    else:
        c_badges = '<span class="badge-cate">기타</span>'

    img_url = get_full_image_url(row.get("img_url"))
    if img_url:
        img_html = f'<img src="{img_url}" class="card-img">'
    else:
        img_html = '<div class="card-img" style="background:#EEE;display:flex;align-items:center;justify-content:center;color:#AAA;">NO IMAGE</div>'

    clean_tag = row.get("reason_tag", "추천")

    preview_html = ""
    if st.session_state.get("debug_mode", False):
        score = safe_int100(row.get("final_score", row.get("total_score", 0)))
        preview_html = f"""
        <div class="preview-bar">
          <span class="preview-label">종합 적합도</span>
          <span class="preview-score">{score}점</span>
        </div>
        """

    st.markdown(
        f"""
        <div class="card-container">
          <div class="card-img-wrapper">{img_html}</div>
          <div class="card-content">
            <div style="margin-bottom:6px;">{d_badge}{c_badges}</div>
            <div class="card-title">{row.get('program_nm', '제목 없음')}</div>
            <div class="user-reason">{clean_tag}</div>
          </div>
          {preview_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("상세보기", key=f"btn_{row.get('contest_pk')}_{key}", use_container_width=True):
        show_detail(row)


@st.dialog("공모전 상세 정보", width="large")
def show_detail(row):
    # ------------------------------------------------
    # 1. 데이터 전처리
    # ------------------------------------------------
    raw_host = row.get('organ_nm')
    if pd.isna(raw_host) or str(raw_host).strip() == "":
        raw_host = row.get('host_company')
    if pd.isna(raw_host) or str(raw_host).strip() == "":
        raw_host = row.get('host_organ', '-')
        
    mapped_host = get_mapped_name(raw_host)

    s_date = str(row.get('putup_sdt', ''))[:10]
    e_date = str(row.get('putup_edt', ''))[:10]
    if not e_date or e_date == 'nan':
        period_str = "상시 모집"
    else:
        period_str = f"{s_date} ~ {e_date}"

    d_day = calc_dday_from_row(row)
    if d_day > 0:
        d_badge = f"D-{d_day}"
        d_color = "#D32F2F"
    elif d_day == 0:
        d_badge = "D-Day"
        d_color = "#D32F2F"
    else:
        d_badge = "마감"
        d_color = "#666"

    field = row.get('분야_한글', '-')
    sub_field = row.get('세부분야_한글')
    if pd.notna(sub_field) and str(sub_field).strip():
        field += f" ({sub_field})"
    
    raw_target = str(row.get('참가자격_한글', ''))
    if pd.isna(raw_target) or raw_target.strip() in ["", "nan", "-"]:
        target = "제한 없음"
    elif "제한 없음" in raw_target or "제한없음" in raw_target:
        # 텍스트 안에 '제한 없음'이 포함되어 있으면 깔끔하게 '제한 없음'으로 통일
        target = "제한 없음"
    else:
        target = raw_target
        
    prize = row.get('prize_money', '-')
    if pd.isna(prize) or str(prize).strip() == "":
        prize = "-"
    
    hit_cnt = f"{row.get('hit', 0):,}"
    
    # ------------------------------------------------
    # 2. UI 렌더링
    # ------------------------------------------------
    
    # [A] 헤더 영역
    st.markdown(
        f"""
        <div class="title-area" style="margin-bottom:12px; border-bottom:none;"> 
            <span style="background-color:{d_color}; color:white; padding:4px 8px; border-radius:4px; font-size:0.8rem; font-weight:bold; vertical-align:middle;">{d_badge}</span>
            <div class="main-title" style="margin-top:8px;">{row.get('program_nm')}</div>
            <div class="sub-info">
                <span>조회수 {hit_cnt}회</span>
                <span>등록일 {s_date}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    Python
# app.py (전체 코드 - show_detail 함수 수정 포함)
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from collections import Counter
from recommender import Recommender

# --------------------------------------------------
# [설정] 기준일 (2023-02-11 시뮬레이션)
# --------------------------------------------------
SIM_NOW = pd.Timestamp("2023-02-11")

# --------------------------------------------------
# 페이지 설정 & CSS
# --------------------------------------------------
st.set_page_config(page_title="씽굿 큐레이션", layout="wide")

st.markdown(
    """<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; color: #333; background-color: #F8F9FA; }
    .stApp { background-color: #F8F9FA; }

    /* 로그인 화면 */
    .login-container { background-color: #FFFFFF; padding: 60px 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); text-align: center; margin-top: 40px; margin-bottom: 40px; border: 1px solid #EAEAEA; }
    .login-title { font-size: 2.0rem; font-weight: 800; color: #222; margin-bottom: 15px; letter-spacing: -0.5px; }
    .login-subtitle { font-size: 1.0rem; color: #666; margin-bottom: 40px; font-weight: 500; }

    /* 버튼 스타일 */
    div.stButton > button { width: 100%; border-radius: 6px; font-weight: 700; padding: 0.5rem 1rem; background-color: #D32F2F !important; color: white !important; border: none !important; }
    div.stButton > button:hover { background-color: #B71C1C !important; }
    button[kind="secondary"] { background-color: #555 !important; color: white !important; border: none !important; }

    /* 카드 스타일 */
    .card-container { background: #FFFFFF; border: 1px solid #EDEDED; border-radius: 12px; overflow: hidden; height: 350px; position: relative; transition: all 0.3s ease; box-shadow: 0 2px 8px rgba(0,0,0,0.03); display: flex; flex-direction: column; }
    .card-container:hover { border-color: #D32F2F; transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.08); }
    .card-img-wrapper { height: 150px; overflow: hidden; background: #F8F9FA; display: flex; align-items: center; justify-content: center; border-bottom: 1px solid #F1F1F1; flex-shrink: 0; }
    .card-img { width: 100%; height: 100%; object-fit: cover; }
    .card-content { padding: 16px; flex-grow: 1; display: flex; flex-direction: column; }

    .badge-dday { font-size: 0.75rem; color: #FFF; background: #D32F2F; padding: 3px 6px; border-radius: 4px; font-weight: 700; margin-right: 4px; vertical-align: middle; }
    .badge-cate { font-size: 0.75rem; color: #555; background: #F1F3F5; padding: 3px 6px; border-radius: 4px; vertical-align: middle; margin-right: 2px;}
    .badge-plus { font-size: 0.7rem; color: #888; border: 1px solid #DDD; padding: 2px 5px; border-radius: 4px; vertical-align: middle; }

    .card-title { font-size: 1rem; font-weight: 700; color: #222; margin-top: 10px; margin-bottom: 8px; height: 2.8em; overflow: hidden; line-height: 1.4; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
    .user-reason { font-size: 0.8rem; color: #D32F2F; font-weight: 700; margin-top: auto; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

    /* 프로필 박스 */
    .profile-box { background:#FFF; padding:15px; border-radius:8px; border:1px solid #E0E0E0; }
    .profile-row { display: flex; margin-top: 5px; font-size: 0.9rem; }
    .profile-label { width: 70px; font-weight: bold; color: #555; }
    .profile-val { flex: 1; color: #333; }

    /* 카드 미리보기 바 */
    .preview-bar { background-color: #263238; padding: 6px 14px; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #37474F; flex-shrink: 0; height: 36px; }
    .preview-label { color: #B0BEC5; font-size: 0.75rem; font-weight: 700; }
    .preview-score { color: #FF5252; font-weight: 900; font-size: 0.9rem; }

    /* 상세 모달: AI 요약 박스 */
    .summary-box {
        background-color: #E3F2FD;
        border-left: 5px solid #1565C0; /* 왼쪽 강조선 추가 */
        border-radius: 4px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .summary-badge {
        background-color: #1565C0;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 8px;
    }
    .summary-text {
        color: #0D47A1;
        font-size: 0.9rem;
        line-height: 1.6;
        font-weight: 500;
    }

    /* 상세 모달: 리포트 스타일 */
    .report-box { background:#263238; color:#fff; padding:16px; border-radius:8px; border:1px solid rgba(255,255,255,0.08); margin-top: 10px; }
    .report-title { font-weight:900; font-size:0.95rem; margin-bottom:12px; color: #ECEFF1; }
    .report-row { display:flex; align-items:center; justify-content:space-between; gap:12px; margin:10px 0; }
    .report-label { width:90px; color:#CFD8DC; font-size:0.85rem; font-weight:700; white-space:nowrap; }
    .report-bar-wrap { flex:1; height:8px; background:#37474F; border-radius:999px; overflow:hidden; }
    .report-bar { height:100%; background:#FF5252; border-radius:999px; }
    .report-val { width:30px; text-align:right; font-weight:900; color:#FFCDD2; font-size:0.85rem; }
    .report-desc { margin-top:12px; color:#B0BEC5; font-size:0.85rem; line-height:1.4; border-top: 1px solid #455A64; padding-top: 10px; }
    .report-total { margin-top:10px; display:flex; justify-content:flex-end; align-items:baseline; gap:8px; }
    .report-total-label { color:#B0BEC5; font-size:0.85rem; font-weight:700; }
    .report-total-score { color:#FF5252; font-size:1.2rem; font-weight:900; }

    /* 상세 페이지 테이블 스타일 */
    .spec-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.95rem;
        margin-bottom: 20px;
    }
    .spec-table td {
        padding: 10px 4px;
        border-bottom: 1px solid #EEEEEE;
        vertical-align: top; /* 텍스트 상단 정렬 */
    }
    .spec-label {
        width: 90px;
        font-weight: 700;
        color: #555;
        background-color: #F9F9F9;
        padding-left: 8px !important;
        border-radius: 4px 0 0 4px;
    }
    .spec-value {
        color: #333;
        padding-left: 12px !important;
        font-weight: 500;
    }
    .title-area {
        margin-bottom: 20px;
        border-bottom: 2px solid #333;
        padding-bottom: 15px;
    }
    .main-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: #111;
        margin-bottom: 8px;
        line-height: 1.3;
    }
    .sub-info {
        font-size: 0.85rem;
        color: #888;
        display: flex;
        gap: 12px;
    }

</style>""",
    unsafe_allow_html=True,
)

# --------------------------------------------------
# 데이터 로드
# --------------------------------------------------
@st.cache_data
def load_data_safe():
    try:
        contest = pd.read_parquet("Contest.parquet")
        user_master = pd.read_parquet("User_Master.parquet")
        user_log = pd.read_parquet("User_Activity_Log.parquet")
        mapping = pd.read_parquet("wnc_category_detail_tb.parquet")
    except Exception as e:
        st.error(f"데이터 로딩 실패: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    if "contest_pk" in contest.columns:
        contest["contest_pk"] = contest["contest_pk"].astype(str)
    if "member_pk" in user_master.columns:
        user_master["member_pk"] = user_master["member_pk"].astype(str)
    if "member_pk" in user_log.columns:
        user_log["member_pk"] = user_log["member_pk"].astype(str)
    if "contest_pk" in user_log.columns:
        user_log["contest_pk"] = user_log["contest_pk"].astype(str)

    for col, default in [("days_since_login", 0), ("n_apply", 0), ("login_cnt", 0), ("CCF_interests", "")]:
        if col not in user_master.columns:
            user_master[col] = default

    user_master["n_apply"] = pd.to_numeric(user_master["n_apply"], errors="coerce").fillna(0).astype(int)
    user_master["login_cnt"] = pd.to_numeric(user_master["login_cnt"], errors="coerce").fillna(0).astype(int)

    if "putup_edt" in contest.columns:
        contest["putup_edt"] = pd.to_datetime(contest["putup_edt"], errors="coerce")

    return contest, user_log, user_master, mapping


contest_df, User_Activity_log, User_Master, map_df = load_data_safe()

# --------------------------------------------------
# 코드 → 한글 매핑 (파일 + 비상용 하드코딩)
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
    "CCFD016": "이벤트", "CCFD017": "취업/창업", "CCFD018": "해외"
}

CODE_MAP = MANUAL_CODES.copy()

if map_df is not None and not map_df.empty:
    if "category_detail_cd" in map_df.columns and "category_detail_nm" in map_df.columns:
        keys = map_df["category_detail_cd"]
        vals = map_df["category_detail_nm"]
    elif len(map_df.columns) >= 5:
        keys = map_df.iloc[:, 2]  # category_detail_cd
        vals = map_df.iloc[:, 4]  # category_detail_nm
    else:
        keys = map_df.iloc[:, 0]
        vals = map_df.iloc[:, 1]
    
    try:
        k_clean = keys.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        v_clean = vals.astype(str).str.strip()
        CODE_MAP.update(dict(zip(k_clean, v_clean)))
    except Exception as e:
        pass


def get_mapped_name(code):
    if pd.isna(code):
        return "-"
    c = str(code).strip().replace(".0", "") 
    return CODE_MAP.get(c, c)


def codes_to_korean(codes_str) -> str:
    if codes_str is None:
        return "-"
    s = str(codes_str).strip()
    if not s or s.lower() == "nan":
        return "-"
    codes = [c.strip() for c in s.split(",") if c.strip()]
    if not codes:
        return "-"
    return ", ".join([get_mapped_name(c) for c in codes])


# --------------------------------------------------
# 추천 엔진
# --------------------------------------------------
@st.cache_resource
def get_engine(user_master, user_log, contest_df):
    if contest_df is None or contest_df.empty:
        return None
    return Recommender(user_master, user_log, contest_df, now_ts=SIM_NOW)


recommender = get_engine(User_Master, User_Activity_log, contest_df)

# --------------------------------------------------
# 세션 상태
# --------------------------------------------------
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "debug_mode" not in st.session_state:
    st.session_state["debug_mode"] = False
if "demo_expected_seg" not in st.session_state:
    st.session_state["demo_expected_seg"] = None
if "cached_recs" not in st.session_state:
    st.session_state["cached_recs"] = None
if "cached_uid" not in st.session_state:
    st.session_state["cached_uid"] = None

# --------------------------------------------------
# 텍스트/전략 정보
# --------------------------------------------------
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
CATEGORIES = [
    "전체",
    "기획/아이디어",
    "광고/마케팅",
    "논문/리포트",
    "영상/UCC/사진",
    "디자인/캐릭터/웹툰",
    "IT/소프트웨어",
    "과학/공학",
    "문학/수기",
    "건축/인테리어",
    "취업/창업",
]
DEMO_ACCOUNTS = [
    ("파워회원(1)", "M22_02522", "POWER"),
    ("파워회원(2)", "M15_01349", "POWER"),
    ("파워회원(3)", "M22_07072", "POWER"),
    ("라이트회원(1)", "M22_05203", "LIGHT"),
    ("라이트회원(2)", "M21_01623", "LIGHT"),
    ("휴면회원", "M10_00108", "DORMANT"),
]
SEGMENT_DISPLAY = {
    "GUEST": "GUEST (비회원)",
    "DORMANT": "DORMANT (휴면 회원)",
    "LIGHT": "LIGHT (라이트 회원)",
    "POWER": "POWER (파워 회원)",
}

# --------------------------------------------------
# 유틸
# --------------------------------------------------
def get_full_image_url(url):
    if pd.isna(url) or str(url) == "nan":
        return None
    url_str = str(url).strip()
    if not url_str:
        return None
    if url_str.startswith("http"):
        return url_str
    if url_str.startswith("/"):
        return f"https://www.thinkcontest.com{url_str}"
    return url_str


def ensure_dday(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    if "putup_edt" in df.columns and "d_day" not in df.columns:
        _today = SIM_NOW
        df = df.copy()
        df["d_day"] = (pd.to_datetime(df["putup_edt"], errors="coerce") - _today).dt.days
    return df


def safe_int100(x):
    try:
        x = float(x)
    except:
        x = 0.0
    x = max(0.0, min(100.0, x))
    return int(round(x))


def clamp01(x):
    try:
        x = float(x)
    except:
        x = 0.0
    return max(0.0, min(1.0, x))


def to100_from01(x):
    return int(round(clamp01(x) * 100))


def urgency_from_dday(d):
    try:
        d = float(d)
    except:
        return 0
    if d <= 0:
        return 100
    if d >= 30:
        return 0
    return int(round((1 - d / 30) * 100))


def calc_dday_from_row(row):
    if "d_day" in row and pd.notna(row.get("d_day")):
        try:
            return int(row.get("d_day"))
        except:
            return 999
    try:
        _today = SIM_NOW
        d = (pd.to_datetime(row.get("putup_edt"), errors="coerce") - _today).days
        return int(d) if pd.notna(d) else 999
    except:
        return 999


# --------------------------------------------------
# 리포트 렌더링
# --------------------------------------------------
def build_report_items(row):
    seg = str(row.get("user_segment", "GUEST")).strip()
    d_day = calc_dday_from_row(row)
    total = safe_int100(row.get("final_score", row.get("total_score", 0)))

    if seg == "POWER":
        h = to100_from01(row.get("norm_history", 0))
        i = to100_from01(row.get("norm_interest", 0))
        p = to100_from01(row.get("norm_pop", 0))
        items = [("이력 유사", h), ("관심 일치", i), ("인기", p)]
        desc = "과거 이력과 관심사를 기반으로 추천했습니다."
        return items, total, desc, seg

    if seg == "LIGHT":
        i = to100_from01(row.get("norm_interest", 0))
        p = to100_from01(row.get("norm_pop", 0))
        items = [("관심 일치", i), ("인기", p)]
        desc = "관심사와 유사한 공모전을 우선 노출했습니다."
        return items, total, desc, seg

    if seg == "DORMANT":
        p = to100_from01(row.get("norm_pop", 0))
        diff = row.get("diff_score", 1.0)
        try:
            diff = float(diff)
        except:
            diff = 1.0
        ease = 100 if diff >= 1.5 else 60
        items = [("입문 난이도", ease), ("인기", p)]
        desc = "부담 없이 시작하기 좋은 EASY 유형입니다."
        return items, total, desc, seg

    pop = to100_from01(row.get("norm_log", row.get("norm_pop", 0)))
    urg = urgency_from_dday(d_day)
    items = [("실시간 인기", pop), ("마감 임박", urg)]
    desc = "최근 사용자들이 많이 찾는 인기 공모전입니다."
    return items, total, desc, "GUEST"


# --------------------------------------------------
# 리포트 박스 렌더링 함수
# --------------------------------------------------
def render_report_box(row):
    items, total_s, desc_txt, seg = build_report_items(row)
    report_rows_html = ""
    for label, val in items[:3]:
        val = int(max(0, min(100, int(val))))
        report_rows_html += f"""
        <div class="report-row">
          <div class="report-label">{label}</div>
          <div class="report-bar-wrap"><div class="report-bar" style="width:{val}%;"></div></div>
          <div class="report-val">{val}</div>
        </div>
        """
    
    st.markdown(
        f"""
        <div class="report-box" style="margin-top:0;">
          <div class="report-title">AI 적합도 리포트</div>
          {report_rows_html}
          <div class="report-desc">{desc_txt}</div>
          <div class="report-total">
            <div class="report-total-label">종합 점수</div>
            <div class="report-total-score">{int(total_s)}점</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# 카드 / 상세 UI
# --------------------------------------------------
def render_card(row, key):
    d = row.get("d_day")
    if pd.isna(d) or d == "":
        d = 999
    try:
        d = int(d)
    except:
        d = 999

    if d >= 0:
        d_badge = f'<span class="badge-dday">D-{d}</span>'
    else:
        d_badge = f'<span class="badge-dday" style="background:#666">D+{abs(d)}</span>'

    raw_cats = str(row.get("분야_한글", ""))
    cats = [c.strip() for c in raw_cats.split(",") if c.strip()]

    if len(cats) > 1:
        c_badges = f'<span class="badge-cate">{cats[0]}</span><span class="badge-plus">+{len(cats)-1}</span>'
    elif len(cats) == 1:
        c_badges = f'<span class="badge-cate">{cats[0]}</span>'
    else:
        c_badges = '<span class="badge-cate">기타</span>'

    img_url = get_full_image_url(row.get("img_url"))
    if img_url:
        img_html = f'<img src="{img_url}" class="card-img">'
    else:
        img_html = '<div class="card-img" style="background:#EEE;display:flex;align-items:center;justify-content:center;color:#AAA;">NO IMAGE</div>'

    clean_tag = row.get("reason_tag", "추천")

    preview_html = ""
    if st.session_state.get("debug_mode", False):
        score = safe_int100(row.get("final_score", row.get("total_score", 0)))
        preview_html = f"""
        <div class="preview-bar">
          <span class="preview-label">종합 적합도</span>
          <span class="preview-score">{score}점</span>
        </div>
        """

    st.markdown(
        f"""
        <div class="card-container">
          <div class="card-img-wrapper">{img_html}</div>
          <div class="card-content">
            <div style="margin-bottom:6px;">{d_badge}{c_badges}</div>
            <div class="card-title">{row.get('program_nm', '제목 없음')}</div>
            <div class="user-reason">{clean_tag}</div>
          </div>
          {preview_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("상세보기", key=f"btn_{row.get('contest_pk')}_{key}", use_container_width=True):
        show_detail(row)


@st.dialog("공모전 상세 정보", width="large")
def show_detail(row):
    # ------------------------------------------------
    # 1. 데이터 전처리
    # ------------------------------------------------
    raw_host = row.get('organ_nm')
    if pd.isna(raw_host) or str(raw_host).strip() == "":
        raw_host = row.get('host_company')
    if pd.isna(raw_host) or str(raw_host).strip() == "":
        raw_host = row.get('host_organ', '-')
        
    mapped_host = get_mapped_name(raw_host)

    s_date = str(row.get('putup_sdt', ''))[:10]
    e_date = str(row.get('putup_edt', ''))[:10]
    if not e_date or e_date == 'nan':
        period_str = "상시 모집"
    else:
        period_str = f"{s_date} ~ {e_date}"

    d_day = calc_dday_from_row(row)
    if d_day > 0:
        d_badge = f"D-{d_day}"
        d_color = "#D32F2F"
    elif d_day == 0:
        d_badge = "D-Day"
        d_color = "#D32F2F"
    else:
        d_badge = "마감"
        d_color = "#666"

    field = row.get('분야_한글', '-')
    sub_field = row.get('세부분야_한글')
    if pd.notna(sub_field) and str(sub_field).strip():
        field += f" ({sub_field})"
    
    # 참가자격 텍스트 정제
    raw_target = str(row.get('참가자격_한글', ''))
    if pd.isna(raw_target) or raw_target.strip() in ["", "nan", "-"]:
        target = "제한 없음"
    elif "제한 없음" in raw_target or "제한없음" in raw_target:
        target = "제한 없음"
    else:
        target = raw_target
        
    prize = row.get('prize_money', '-')
    if pd.isna(prize) or str(prize).strip() == "":
        prize = "-"
    
    hit_cnt = f"{row.get('hit', 0):,}"
    
    # ------------------------------------------------
    # 2. UI 렌더링
    # ------------------------------------------------
    
    # [A] 헤더 영역 (타이틀)
    st.markdown(
        f"""
        <div class="title-area" style="margin-bottom:20px; border-bottom:2px solid #333;"> 
            <span style="background-color:{d_color}; color:white; padding:4px 8px; border-radius:4px; font-size:0.8rem; font-weight:bold; vertical-align:middle;">{d_badge}</span>
            <div class="main-title" style="margin-top:8px;">{row.get('program_nm')}</div>
            <div class="sub-info">
                <span>조회수 {hit_cnt}회</span>
                <span>등록일 {s_date}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # [B] 본문 레이아웃 (2단 구성)
    c1, c2 = st.columns([1, 1.3])
    
    # --- 좌측: 포스터 이미지 ---
    with c1:
        img_url = get_full_image_url(row.get("img_url"))
        if img_url:
            st.image(img_url, use_container_width=True)
        else:
            st.markdown(
                """<div style="width:100%; height:350px; background:#F0F0F0; display:flex; 
                align-items:center; justify-content:center; color:#AAA; border-radius:8px;">
                이미지 없음</div>""", 
                unsafe_allow_html=True
            )

    # --- 우측: 스펙 테이블 + 버튼 + AI 분석 ---
    with c2:
        # 1. 스펙 테이블
        table_html = f"""
        <table class="spec-table">
            <tr>
                <td class="spec-label">분야</td>
                <td class="spec-value">{field}</td>
            </tr>
            <tr>
                <td class="spec-label">주최/주관</td>
                <td class="spec-value">{mapped_host}</td>
            </tr>
            <tr>
                <td class="spec-label">참가자격</td>
                <td class="spec-value">{target}</td>
            </tr>
            <tr>
                <td class="spec-label">접수기간</td>
                <td class="spec-value">{period_str}</td>
            </tr>
            <tr>
                <td class="spec-label">시상내역</td>
                <td class="spec-value">{prize}</td>
            </tr>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)
        
        # 2. 홈페이지 바로가기 버튼
        home_url = row.get('hompage_url')
        if pd.notna(home_url) and str(home_url).strip():
             st.link_button("홈페이지 바로가기", home_url, use_container_width=True, type="primary")
        else:
             st.button("홈페이지 정보 없음", disabled=True, use_container_width=True)

        # ------------------------------------------------
        # [C] AI 분석 리포트 (우측 컬럼, 버튼 바로 아래 배치)
        # ------------------------------------------------
        
        # 구분용 여백
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("#### 🤖 AI 추천 분석")

        tag = row.get("reason_tag", "")
        clean_tag = tag 

        summary_txt = ""
        if row.get("ai_summary"):
            summary_txt = str(row.get("ai_summary"))
            for code, name in CODE_MAP.items():
                if code and code in summary_txt:
                    summary_txt = summary_txt.replace(code, name)
        
        # (1) 요약 박스
        if tag or summary_txt:
            st.markdown(
                f"""
                <div class="summary-box" style="margin-top: 5px;">
                    <span class="summary-badge">{clean_tag}</span>
                    <div class="summary-text">{summary_txt}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # (2) 상세 분석 탭 (분석 모드 ON일 때만)
        if st.session_state.get("debug_mode", False):
            tab1, tab2 = st.tabs(["적합도 상세", "점수 산출식"])
            with tab1:
                render_report_box(row)
            with tab2:
                raw_score = float(row.get("raw_score", row.get("algo_score", 0.0)))
                final_score = safe_int100(row.get("final_score", row.get("total_score", 0)))
                seg_max = float(row.get("seg_max_score", 1.0))
                segment = str(row.get("user_segment", "GUEST"))

                # 컴포넌트 값 가져오기
                nh = float(row.get("norm_history", 0.0))
                ni = float(row.get("norm_interest", 0.0))
                npop = float(row.get("norm_pop", 0.0))
                nlog = float(row.get("norm_log", 0.0))
                diff = float(row.get("diff_score", 1.0))

                # 세그먼트별 HTML 생성
                calc_html = ""
                
                # 스타일 정의 (내부용)
                row_style = "display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.1);"
                label_style = "color:#B0BEC5; font-size:0.9rem; font-weight:600;"
                val_style = "color:#FFF; font-size:0.9rem;"
                res_style = "color:#FFCDD2; font-weight:bold; font-size:0.95rem;"

                if segment == "POWER":
                    # 1.5*이력 + 1.0*관심 + 0.3*인기
                    calc_html = f"""
                    <div style="{row_style}">
                        <span style="{label_style}">이력 유사도</span>
                        <span style="{val_style}">{nh:.2f} × <span style="color:#90A4AE; font-size:0.8rem;">1.5 (가중치)</span></span>
                        <span style="{res_style}">+ {(nh*1.5):.2f}</span>
                    </div>
                    <div style="{row_style}">
                        <span style="{label_style}">관심 일치도</span>
                        <span style="{val_style}">{ni:.2f} × <span style="color:#90A4AE; font-size:0.8rem;">1.0 (가중치)</span></span>
                        <span style="{res_style}">+ {(ni*1.0):.2f}</span>
                    </div>
                    <div style="{row_style}">
                        <span style="{label_style}">대중 인기도</span>
                        <span style="{val_style}">{npop:.2f} × <span style="color:#90A4AE; font-size:0.8rem;">0.3 (가중치)</span></span>
                        <span style="{res_style}">+ {(npop*0.3):.2f}</span>
                    </div>
                    """
                elif segment == "LIGHT":
                    # 1.0*관심 + 0.3*인기
                    calc_html = f"""
                    <div style="{row_style}">
                        <span style="{label_style}">관심 일치도</span>
                        <span style="{val_style}">{ni:.2f} × <span style="color:#90A4AE; font-size:0.8rem;">1.0 (가중치)</span></span>
                        <span style="{res_style}">+ {(ni*1.0):.2f}</span>
                    </div>
                    <div style="{row_style}">
                        <span style="{label_style}">대중 인기도</span>
                        <span style="{val_style}">{npop:.2f} × <span style="color:#90A4AE; font-size:0.8rem;">0.3 (가중치)</span></span>
                        <span style="{res_style}">+ {(npop*0.3):.2f}</span>
                    </div>
                    """
                elif segment == "DORMANT":
                    # 인기 * 난이도
                    calc_html = f"""
                    <div style="{row_style}">
                        <span style="{label_style}">대중 인기도</span>
                        <span style="{val_style}">{npop:.2f}</span>
                        <span style="{res_style}">{npop:.2f}</span>
                    </div>
                    <div style="{row_style}">
                        <span style="{label_style}">난이도 가중치</span>
                        <span style="{val_style}">{diff:.1f} <span style="color:#90A4AE; font-size:0.8rem;">(Easy=2.0)</span></span>
                        <span style="{res_style}">× {diff:.1f}</span>
                    </div>
                    """
                else: # GUEST
                    # 0.7*로그 + 0.3*조회
                    calc_html = f"""
                    <div style="{row_style}">
                        <span style="{label_style}">실시간 클릭</span>
                        <span style="{val_style}">{nlog:.2f} × <span style="color:#90A4AE; font-size:0.8rem;">0.7 (가중치)</span></span>
                        <span style="{res_style}">+ {(nlog*0.7):.2f}</span>
                    </div>
                    <div style="{row_style}">
                        <span style="{label_style}">누적 조회수</span>
                        <span style="{val_style}">{npop:.2f} × <span style="color:#90A4AE; font-size:0.8rem;">0.3 (가중치)</span></span>
                        <span style="{res_style}">+ {(npop*0.3):.2f}</span>
                    </div>
                    """

                # 최종 렌더링 (카드 + 환산식)
                st.markdown(
                    f"""
                    <div class="report-box" style="margin-top:0; padding:16px;">
                      <div style="margin-bottom:12px; color:#CFD8DC; font-size:0.85rem; font-weight:700; border-bottom:1px solid #546E7A; padding-bottom:4px;">
                        STEP 1. 알고리즘 점수 합산
                      </div>
                      {calc_html}
                      <div style="margin-top:8px; text-align:right; color:#FFF; font-weight:bold; font-size:1.1rem;">
                        = {raw_score:.4f} <span style="font-size:0.8rem; color:#90A4AE;">(Raw)</span>
                      </div>

                      <div style="margin-top:20px; margin-bottom:12px; color:#CFD8DC; font-size:0.85rem; font-weight:700; border-bottom:1px solid #546E7A; padding-bottom:4px;">
                        STEP 2. 100점 만점 환산
                      </div>
                      <div style="background:rgba(0,0,0,0.2); padding:10px; border-radius:6px; display:flex; align-items:center; justify-content:center; gap:10px;">
                         <div style="text-align:center;">
                            <span style="font-size:1.1rem; font-weight:bold; color:#FFF;">{raw_score:.2f}</span>
                         </div>
                         <div style="color:#90A4AE;">÷</div>
                         <div style="text-align:center;">
                            <span style="font-size:1.1rem; font-weight:bold; color:#B0BEC5;">{seg_max:.1f}</span>
                            <span style="font-size:0.7rem; display:block; color:#546E7A;">Max</span>
                         </div>
                         <div style="color:#90A4AE;">× 100 = </div>
                         <div style="text-align:center;">
                             <span style="font-size:1.4rem; font-weight:900; color:#FF5252;">{final_score}점</span>
                         </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
# --------------------------------------------------
# 사이드바 & 메인 로직
# --------------------------------------------------
def login_demo(uid, expected_seg=None):
    st.session_state["user_id"] = uid
    st.session_state["demo_expected_seg"] = expected_seg
    st.session_state["cached_recs"] = None # 로그인 시 캐시 초기화
    st.rerun()


with st.sidebar:
    st.header("관리자 메뉴")
    st.toggle("분석 모드", key="debug_mode")
    st.divider()

    with st.expander("시연 계정 접속", expanded=True):
        if User_Master is None or User_Master.empty:
            st.error("User_Master 데이터 없음")
        else:
            for label, uid, expected_seg in DEMO_ACCOUNTS:
                if st.button(label, use_container_width=True):
                    login_demo(uid, expected_seg)

    current_uid = st.session_state.get("user_id")
    display_id = current_uid if current_uid else "GUEST"

    seg = recommender.identify_segment(display_id) if recommender else "GUEST"
    strat_info = STRATEGY_INFO.get(seg, STRATEGY_INFO["GUEST"])
    display_seg_name = SEGMENT_DISPLAY.get(seg, seg)

    expected = st.session_state.get("demo_expected_seg")
    if expected:
        if seg == expected:
            st.success(f"DEMO 검증: {expected} 정상 판별")
        else:
            st.warning(
                f"DEMO 검증 불일치 (기대={expected} / 실제={seg})\n\n"
                f"- User_Master의 n_apply / days_since_login / CCF_interests 확인\n"
                f"- member_pk / contest_pk 타입(str) 일치 여부 확인"
            )

    interest_txt = "-"
    apply_info_txt = "지원 이력 없음"
    apply_cnt = 0

    if current_uid and recommender:
        u = recommender.users[recommender.users["member_pk"] == display_id]
        if not u.empty:
            interest_txt = codes_to_korean(u.iloc[0].get("CCF_interests", ""))
            apply_cnt = int(u.iloc[0].get("n_apply", 0))

            if apply_cnt > 0 and User_Activity_log is not None and not User_Activity_log.empty:
                user_logs = User_Activity_log[User_Activity_log["member_pk"] == display_id]
                applied_pks = user_logs["contest_pk"].astype(str).unique()
                applied_contests = contest_df[contest_df["contest_pk"].astype(str).isin(applied_pks)]

                if not applied_contests.empty and "분야_한글" in applied_contests.columns:
                    fields = []
                    for f_str in applied_contests["분야_한글"].dropna():
                        fields.extend([f.strip() for f in str(f_str).split(",") if f.strip()])
                    if fields:
                        counts = Counter(fields).most_common(3)
                        apply_info_txt = ", ".join([f"{k}({v})" for k, v in counts])
                    else:
                        apply_info_txt = f"총 {apply_cnt}회 지원"
                else:
                    apply_info_txt = f"총 {apply_cnt}회 지원"

    st.divider()
    st.markdown("### 내 프로필")
    st.markdown(
        f"""
        <div class="profile-box">
            <div class="profile-row">
                <div class="profile-label">ID</div>
                <div class="profile-val">{display_id}</div>
            </div>
            <div class="profile-row">
                <div class="profile-label">유형</div>
                <div class="profile-val" style="color:#D32F2F; font-weight:bold;">{display_seg_name}</div>
            </div>
            <div class="profile-row">
                <div class="profile-label">활동</div>
                <div class="profile-val">
                    <div style="font-weight:bold;">총 {apply_cnt}회 지원</div>
                    <div style="font-size:0.8rem; color:#666;">{apply_info_txt}</div>
                </div>
            </div>
            <div class="profile-row">
                <div class="profile-label">관심사</div>
                <div class="profile-val" style="font-size:0.85rem;">{interest_txt}</div>
            </div>
            <hr style="margin:10px 0; border:0; border-top:1px dashed #DDD;">
            <div style="font-weight:bold; font-size:0.85rem;">적용 알고리즘</div>
            <div style="background:#F8F9FA; padding:8px; border-radius:4px; font-size:0.8rem; margin-top:5px;">{strat_info['method']}</div>
            <div style="margin-top:10px; font-weight:bold; font-size:0.85rem;">로직 설명</div>
            <div style="background:#F8F9FA; padding:8px; border-radius:4px; font-size:0.8rem; margin-top:5px; line-height:1.4;">{strat_info['desc']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if not recommender:
    st.error("Data Load Error")
    st.stop()

# --------------------------------------------------
# 메인 화면
# --------------------------------------------------
if not st.session_state["user_id"]:
    c1, c2, c3 = st.columns([1, 10, 1])
    with c2:
        st.markdown(
            """
            <div class="login-container">
                <div class="login-title">누구나 도전을 꿈꾸고 경험하도록</div>
                <div class="login-subtitle">오늘 더 나은 세상을 만들어 갑니다.</div>
            """,
            unsafe_allow_html=True,
        )

        uid_input = st.text_input("ID", placeholder="M24_...", label_visibility="collapsed")
        if st.button("시작하기", use_container_width=True):
            if not uid_input:
                st.warning("아이디를 입력해주세요.")
            elif not uid_input.strip().startswith("M"):
                st.error("잘못된 아이디 형식입니다. 'M'으로 시작하는 아이디를 입력해주세요.")
            else:
                st.session_state["user_id"] = uid_input.strip()
                st.session_state["demo_expected_seg"] = None
                st.session_state["cached_recs"] = None # 로그인 시 캐시 초기화
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 4])
    with col_l:
        cat = st.radio("관심 분야", CATEGORIES)

    with col_r:
        st.subheader(f"{cat} 인기 공모전")
        recs, *_ = recommender.get_recommendations("GUEST", top_n=30)
        recs = ensure_dday(recs)

        if recs is not None and not recs.empty:
            final_recs = recs.copy()
            if cat != "전체" and "분야_한글" in recs.columns:
                filtered = recs[recs["분야_한글"].astype(str).str.contains(str(cat), na=False)]
                if len(filtered) < 4:
                    st.error(f"'{cat}' 분야 공모전이 부족하여, 전체 인기 공모전을 보여드립니다.")
                else:
                    final_recs = filtered

            final_recs = final_recs.head(8)
            cols = st.columns(4)
            for i, (_, row) in enumerate(final_recs.iterrows()):
                with cols[i % 4]:
                    render_card(row, "g")
        else:
            st.warning("추천 결과 없음")

else:
    uid = st.session_state["user_id"]
    c_head, c_btn = st.columns([8, 1])
    with c_head:
        st.markdown(f"### 안녕하세요, {uid}님!")
    with c_btn:
        if st.button("Logout"):
            st.session_state["user_id"] = None
            st.session_state["demo_expected_seg"] = None
            st.session_state["cached_recs"] = None
            st.rerun()

    # 추천 결과 세션에 캐싱
    if st.session_state["cached_recs"] is None or st.session_state["cached_uid"] != uid:
        recs, *_ = recommender.get_recommendations(uid, top_n=12)
        recs = ensure_dday(recs)
        st.session_state["cached_recs"] = recs
        st.session_state["cached_uid"] = uid
    else:
        recs = st.session_state["cached_recs"]

    if recs is not None and not recs.empty:
        st.markdown("#### 오늘의 맞춤 추천")
        cols = st.columns(4)
        for i, (_, row) in enumerate(recs.head(4).iterrows()):
            with cols[i]:
                render_card(row, "t")

        st.markdown("#### 놓치면 아쉬운 발견")
        cols = st.columns(4)
        for i, (_, row) in enumerate(recs.iloc[4:].iterrows()):
            with cols[i % 4]:
                render_card(row, "d")
    else:
        st.warning("추천 결과가 없습니다.")
