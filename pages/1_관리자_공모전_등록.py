# pages/1_관리자_공모전_등록.py
import streamlit as st
import pandas as pd

from admin.constants import (
    STATUS_OPTIONS, HOST_ORG_TYPES, KEYWORD_TAGS, CONTEST_FIELDS, REGIONS, APPLY_METHOD_TYPES
)
from admin.eligibility_parser import parse_eligibility
from admin.keyword_extractor import extract_keywords
from admin.schema import build_record

st.set_page_config(page_title="관리자 | 공모전 등록", layout="wide")

# -----------------------
# 0) 관리자 모드 게이트
# -----------------------
st.sidebar.markdown("## 관리자 메뉴")
admin_mode = st.sidebar.checkbox("관리자 모드 ON", value=st.session_state.get("admin_mode", False))
st.session_state["admin_mode"] = admin_mode

if not admin_mode:
    st.warning("관리자 모드가 OFF 상태입니다. 좌측 사이드바에서 **관리자 모드 ON**을 체크해 주세요.")
    st.stop()

# -----------------------
# 1) 데모용 마스터 데이터(주최사/담당자) - 세션에만 유지
# -----------------------
if "companies" not in st.session_state:
    st.session_state["companies"] = ["씽굿", "KOSA", "OO대학교", "OO재단"]
if "managers" not in st.session_state:
    st.session_state["managers"] = ["admin01", "manager02", "staff03"]
if "contest_records" not in st.session_state:
    st.session_state["contest_records"] = []  # list[dict]

st.title("관리자용 공모전 등록 (정형 데이터 중심 · 데모용)")

colA, colB = st.columns([2, 1], gap="large")

with colA:
    st.subheader("기본 정보")

    with st.form("contest_form", clear_on_submit=False):
        status = st.radio("상태(status)", STATUS_OPTIONS, horizontal=True)

        host_org_types = st.multiselect("주최기관(정형 선택)", HOST_ORG_TYPES)

        # ---- 주최사: 검색 선택 + 신규 추가(세션에만 저장) ----
        st.markdown("### 주최사(검색 선택 / 신규 추가)")
        company_search = st.text_input("주최사 검색", placeholder="예: 씽굿 / OO재단")
        filtered_companies = [c for c in st.session_state["companies"] if company_search.strip() in c] if company_search else st.session_state["companies"]
        host_company = st.selectbox("기존 목록에서 선택", options=filtered_companies if filtered_companies else ["(검색 결과 없음)"])
        new_company = st.text_input("목록에 없으면 신규 주최사 입력(선택)", placeholder="예: 새 주최사명")

        homepage_url = st.text_input("홈페이지 URL", placeholder="https://...")

        keywords = st.multiselect("키워드(정형 선택)", KEYWORD_TAGS)
        project_name = st.text_input("프로젝트명(text)", placeholder="예: 2026 AI 아이디어 공모전")

        apply_start_date = st.date_input("접수 시작일", value=None)
        apply_end_date = st.date_input("접수 마감일", value=None)
        extended_end_date = st.date_input("연장 기간(연장 마감일)", value=None)

        fields = st.multiselect("공모 분야(정형 선택)", CONTEST_FIELDS)

        st.markdown("### 참가 자격(자동 정형화)")
        eligibility_raw = st.text_input(
            "참가자격 원문 입력",
            placeholder="예: 만 19세 이상, 19세~39세, 청소년, 대학생 등"
        )

        apply_method_type = st.selectbox("접수 방법(유형)", APPLY_METHOD_TYPES)
        apply_method_url = st.text_input("접수 방법 링크(URL)", placeholder="https://...")

        region = st.selectbox("참가 지역(정형)", ["(선택)"] + REGIONS)

        prize_1st_amount = st.number_input("시상 규모(1등 시상금 정확한 금액)", min_value=0, step=10000)

        st.markdown("### 포스터(업로드만, 실제 저장 X)")
        poster = st.file_uploader("포스터 파일 업로드", type=["png", "jpg", "jpeg", "webp"])

        # ---- 담당자: 검색 선택 + 신규 추가(세션) ----
        st.markdown("### 담당자(검색 선택 / 신규 추가)")
        manager_search = st.text_input("담당자 ID 검색", placeholder="예: admin01")
        filtered_mgrs = [m for m in st.session_state["managers"] if manager_search.strip() in m] if manager_search else st.session_state["managers"]
        manager_id = st.selectbox("기존 목록에서 선택", options=filtered_mgrs if filtered_mgrs else ["(검색 결과 없음)"])
        new_manager = st.text_input("목록에 없으면 신규 담당자 ID 입력(선택)", placeholder="예: new_admin")

        st.divider()
        st.subheader("공모요강(컬럼은 고정, 내용은 텍스트)")
        guide_apply_part = st.text_area("응모 부분", height=80)
        guide_topic = st.text_area("응모 주제", height=80)
        guide_prize_detail = st.text_area("시상 내역", height=80)
        guide_schedule = st.text_area("응모 일정", height=80)
        guide_submit_method = st.text_area("제출 방법", height=80)
        guide_judging_criteria = st.text_area("심사 기준", height=80)
        guide_notes = st.text_area("유의 사항", height=100)

        submitted = st.form_submit_button("등록(데모)")

    # ---- 등록 처리 ----
    if submitted:
        # 신규 주최사/담당자 처리(세션에만 추가)
        if new_company.strip():
            if new_company.strip() not in st.session_state["companies"]:
                st.session_state["companies"].append(new_company.strip())
            host_company_final = new_company.strip()
        else:
            host_company_final = host_company if host_company != "(검색 결과 없음)" else ""

        if new_manager.strip():
            if new_manager.strip() not in st.session_state["managers"]:
                st.session_state["managers"].append(new_manager.strip())
            manager_final = new_manager.strip()
        else:
            manager_final = manager_id if manager_id != "(검색 결과 없음)" else ""

        # 참가자격 자동 파싱
        age_min, age_max, condition_type, keyword_hit = parse_eligibility(eligibility_raw)

        # AI 키워드(가벼운 데모): 프로젝트명+요강 합쳐서 추출
        combined_text = " ".join([
            project_name or "",
            guide_apply_part or "", guide_topic or "", guide_prize_detail or "",
            guide_schedule or "", guide_submit_method or "", guide_judging_criteria or "",
            guide_notes or ""
        ])
        ai_keywords = extract_keywords(combined_text, top_k=8)

        payload = {
            "status": status,
            "host_org_types": host_org_types,          # list
            "host_company": host_company_final,        # text(마스터 참조라고 가정)
            "homepage_url": homepage_url,
            "keywords": keywords,                       # list (정형)
            "project_name": project_name,
            "apply_start_date": apply_start_date,
            "apply_end_date": apply_end_date,
            "extended_end_date": extended_end_date,
            "fields": fields,                           # list
            "eligibility_raw": eligibility_raw,
            "eligibility_age_min": age_min,
            "eligibility_age_max": age_max,
            "eligibility_condition_type": condition_type,
            "eligibility_keyword": keyword_hit,
            "apply_method_type": apply_method_type,
            "apply_method_url": apply_method_url,
            "region": None if region == "(선택)" else region,
            "prize_1st_amount": int(prize_1st_amount),
            "poster_filename": poster.name if poster else None,  # 저장은 안 하고 이름만
            "manager_id": manager_final,
            # 요강(컬럼 고정)
            "guide_apply_part": guide_apply_part,
            "guide_topic": guide_topic,
            "guide_prize_detail": guide_prize_detail,
            "guide_schedule": guide_schedule,
            "guide_submit_method": guide_submit_method,
            "guide_judging_criteria": guide_judging_criteria,
            "guide_notes": guide_notes,
            # AI 추출
            "ai_keywords": ai_keywords,
        }

        record = build_record(payload)
        st.session_state["contest_records"].append(record)

        st.success("✅ 데모 등록 완료! (세션에만 저장됩니다)")
        st.json({
            "eligibility_parsed": {
                "age_min": age_min, "age_max": age_max,
                "condition_type": condition_type, "keyword_hit": keyword_hit
            },
            "ai_keywords": ai_keywords
        })

        if poster:
            st.info("포스터는 **실제 저장하지 않고**, 미리보기만 제공합니다.")
            st.image(poster, use_container_width=True)

with colB:
    st.subheader("등록된 데이터(세션)")
    if st.session_state["contest_records"]:
        df = pd.DataFrame(st.session_state["contest_records"])

        st.dataframe(df, use_container_width=True)

        # 데모용 CSV 다운로드(실제 저장은 아니지만, 시연에서 강력합니다)
        csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "등록 데이터 CSV 다운로드(데모)",
            data=csv_bytes,
            file_name="demo_contests.csv",
            mime="text/csv"
        )

        if st.button("세션 데이터 초기화(데모)"):
            st.session_state["contest_records"] = []
            st.success("초기화 완료")
            st.rerun()
    else:
        st.caption("아직 등록된 데이터가 없습니다. 왼쪽에서 등록해 보세요.")

    st.divider()
    st.subheader("마스터 목록(데모)")
    st.write("**주최사 목록(세션):**", st.session_state["companies"])
    st.write("**담당자 목록(세션):**", st.session_state["managers"])
