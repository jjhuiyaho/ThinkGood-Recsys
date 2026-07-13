# recommender.py
import pandas as pd
import numpy as np
from datetime import datetime


class Recommender:
    """
    세그먼트 기반 공모전 추천 엔진

    [세그먼트]
    - DORMANT: days_since_login > 1080
    - POWER  : n_apply >= 2
    - LIGHT  : CCF_interests 존재
    - GUEST  : 그 외 (또는 user_id가 User_Master에 없음)

    [점수 구성]
    - POWER  : 1.5*norm_history + 1.0*norm_interest + 0.3*norm_pop
    - LIGHT  : 1.0*norm_interest + 0.3*norm_pop
    - DORMANT: norm_pop * diff_score (EASY=2.0, else=1.0)
    - GUEST  : 0.7*norm_log + 0.3*norm_pop

    [출력 컬럼]
    - algo_score   : 가중합 raw (정규화된 컴포넌트 기반)
    - raw_score    : algo_score와 동일하게 제공
    - final_score  : (algo_score / theoretical_max)*100  (상대평가가 아닌 납득 가능한 비율)
    - seg_max_score: 이론상 최대 점수 (점수 산출 설명용)
    - reason_tag   : "취향 저격" / "입문 추천" / "지금 인기"
    - ai_summary   : 추천 설명 멘트
    - contrib_text : "이력 55% · 관심 35% · 인기 10%" 같은 기여도 요약(가능한 세그먼트만)
    - dominant_factor : "이력 기반" / "관심 기반" / "인기 기반" / "로그 기반" 등
    """

    def __init__(self, user_df: pd.DataFrame, log_df: pd.DataFrame, contest_df: pd.DataFrame, now_ts=None):
        self.users = user_df.copy()
        self.logs = log_df.copy()
        self.contests = contest_df.copy()

        # --- 과거 시점 시뮬레이션용 기준 시각(now) ---
        # now_ts가 주어지면 해당 시점 기준으로 '모집중(putup_edt>=now)' 필터와 D-day를 계산합니다.
        self.now = pd.Timestamp(now_ts) if now_ts is not None else pd.Timestamp(datetime.now())

        # --- user 최소 전처리 ---
        if "n_apply" not in self.users.columns:
            self.users["n_apply"] = 0
        if "login_cnt" not in self.users.columns:
            self.users["login_cnt"] = 0
        if "days_since_login" not in self.users.columns:
            self.users["days_since_login"] = 0
        if "CCF_interests" not in self.users.columns:
            self.users["CCF_interests"] = ""

        self.users["n_apply"] = pd.to_numeric(self.users["n_apply"], errors="coerce").fillna(0).astype(int)
        self.users["login_cnt"] = pd.to_numeric(self.users["login_cnt"], errors="coerce").fillna(0).astype(int)
        self.users["days_since_login"] = pd.to_numeric(self.users["days_since_login"], errors="coerce").fillna(0)

        # --- log 최소 전처리 ---
        if "contest_pk" in self.logs.columns:
            self.logs["contest_pk"] = self.logs["contest_pk"].astype(str)
        if "member_pk" in self.logs.columns:
            self.logs["member_pk"] = self.logs["member_pk"].astype(str)

        # --- contest 최소 전처리 ---
        if "contest_pk" in self.contests.columns:
            self.contests["contest_pk"] = self.contests["contest_pk"].astype(str)

        self._preprocess()
        self._build_main_idf()

    # ---------------------------------------------------------
    # [전처리] 인기도/난이도/로그 인기
    # ---------------------------------------------------------
    def _preprocess(self):
        # hit -> hit_num
        self.contests["hit_num"] = pd.to_numeric(self.contests.get("hit", 0), errors="coerce").fillna(0.0)

        # 로그 기반 인기
        if "contest_pk" in self.logs.columns and not self.logs.empty:
            self.log_pop_by_contest = self.logs["contest_pk"].value_counts().astype(float)
        else:
            self.log_pop_by_contest = pd.Series(dtype=float)

        # 난이도 자동 판정
        def get_difficulty(row):
            text = f"{row.get('program_nm','')} {row.get('분야_한글','')}"
            easy_kw = ["네이밍", "슬로건", "사진", "설문", "아이디어", "퀴즈"]
            hard_kw = ["논문", "개발", "해커톤", "건축", "학술", "설계"]
            if any(x in str(text) for x in easy_kw):
                return "EASY"
            if any(x in str(text) for x in hard_kw):
                return "HARD"
            return "NORMAL"

        self.contests["difficulty"] = self.contests.apply(get_difficulty, axis=1)

    # ---------------------------------------------------------
    # [유틸]
    # ---------------------------------------------------------
    def _split_codes(self, x) -> set:
        if pd.isna(x) or str(x).strip() == "" or str(x).lower() == "nan":
            return set()
        return set([t.strip() for t in str(x).split(",") if t.strip()])

    def _get_contest_fields(self, contest_pk: str) -> set:
        row = self.contests[self.contests["contest_pk"] == str(contest_pk)]
        if not row.empty:
            return self._split_codes(row.iloc[0].get("contest_field", ""))
        return set()

    def _safe_norm(self, series: pd.Series) -> pd.Series:
        if series is None or len(series) == 0:
            return pd.Series([], dtype=float)
        m = float(series.max()) if len(series) else 0.0
        if m <= 0:
            return pd.Series(0.0, index=series.index)
        return series / m

    def _build_main_idf(self):
        if "contest_field" not in self.contests.columns:
            self.main_idf = {}
            return

        main_series = self.contests["contest_field"].astype(str).str.split(",").explode().str.strip()
        main_series = main_series[main_series != ""]
        if not main_series.empty:
            freq = main_series.value_counts()
            self.main_idf = (np.log((len(self.contests) + 1) / (freq + 1)) + 1.0).to_dict()
        else:
            self.main_idf = {}

    def _base_candidates(self):
        today = self.now
        cands = self.contests.copy()

        # 모집 중만 (putup_edt가 없거나 미래)
        if "putup_edt" in cands.columns:
            cands["putup_edt"] = pd.to_datetime(cands["putup_edt"], errors="coerce")
            cands = cands[(cands["putup_edt"].isna()) | (cands["putup_edt"] >= today)]
        return cands, today

    # ---------------------------------------------------------
    # [세그먼트 판별]
    # ---------------------------------------------------------
    def identify_segment(self, user_id: str) -> str:
        pk = str(user_id)
        if pk not in self.users["member_pk"].astype(str).values:
            return "GUEST"

        user = self.users[self.users["member_pk"].astype(str) == pk].iloc[0]
        apply = int(user.get("n_apply", 0))
        days = user.get("days_since_login", 0)
        interests_val = str(user.get("CCF_interests", ""))
        has_interest = pd.notna(user.get("CCF_interests")) and len(interests_val.strip()) > 1

        if pd.notna(days) and float(days) > 1080:
            return "DORMANT"
        if apply >= 2:
            return "POWER"
        if has_interest:
            return "LIGHT"
        return "GUEST"

    # ---------------------------------------------------------
    # [추천 로직] POWER
    # ---------------------------------------------------------
    def _recommend_power(self, user_id: str, top_n=6):
        cands, _ = self._base_candidates()

        user_row = self.users[self.users["member_pk"].astype(str) == str(user_id)].iloc[0]
        user_logs = self.logs[self.logs["member_pk"].astype(str) == str(user_id)] if not self.logs.empty else pd.DataFrame()

        applied_pks = set(user_logs["contest_pk"].astype(str).tolist()) if not user_logs.empty else set()
        user_interests = self._split_codes(user_row.get("CCF_interests", ""))

        # 이력 프로필(IDF 가중)
        history_profile = {}
        for cp in applied_pks:
            fields = self._get_contest_fields(cp)
            for f in fields:
                history_profile[f] = history_profile.get(f, 0.0) + float(self.main_idf.get(f, 1.0))

        # 이미 지원한 공모전 제외
        if "contest_pk" in cands.columns and applied_pks:
            cands = cands[~cands["contest_pk"].astype(str).isin(applied_pks)].copy()

        # 분야 개수 보정(분야 많을수록 점수 패널티)
        def get_adjusted_score(row_fields, profile_dict):
            target_fields = self._split_codes(row_fields)
            if not target_fields:
                return 0.0
            raw_score = sum(profile_dict.get(f, 0.0) for f in target_fields)
            penalty = np.sqrt(len(target_fields))
            return raw_score / penalty

        cands["score_history"] = [get_adjusted_score(cf, history_profile) for cf in cands.get("contest_field", "")]
        interest_profile = {f: float(self.main_idf.get(f, 1.0)) for f in user_interests}
        cands["score_interest"] = [get_adjusted_score(cf, interest_profile) for cf in cands.get("contest_field", "")]
        cands["score_pop"] = np.log1p(cands["hit_num"])

        # 정규화 컴포넌트
        cands["norm_history"] = self._safe_norm(cands["score_history"])
        cands["norm_interest"] = self._safe_norm(cands["score_interest"])
        cands["norm_pop"] = self._safe_norm(cands["score_pop"])

        # 가중합 점수
        cands["algo_score"] = (
            1.5 * cands["norm_history"]
            + 1.0 * cands["norm_interest"]
            + 0.3 * cands["norm_pop"]
        )

        return cands, "POWER: 개인화 하이브리드(이력+관심+인기, 분야 보정 적용)"

    # ---------------------------------------------------------
    # [추천 로직] LIGHT
    # ---------------------------------------------------------
    def _recommend_light(self, user_id: str, top_n=6):
        cands, _ = self._base_candidates()
        user_interests = self._split_codes(
            self.users[self.users["member_pk"].astype(str) == str(user_id)].iloc[0].get("CCF_interests", "")
        )

        cands["score_interest"] = [
            sum(float(self.main_idf.get(f, 0.0)) for f in (user_interests & self._split_codes(cf)))
            for cf in cands.get("contest_field", "")
        ]
        cands["score_pop"] = np.log1p(cands["hit_num"])

        cands["norm_interest"] = self._safe_norm(cands["score_interest"])
        cands["norm_pop"] = self._safe_norm(cands["score_pop"])

        cands["algo_score"] = cands["norm_interest"] + 0.3 * cands["norm_pop"]
        return cands, "LIGHT: 관심사 기반 매칭(+인기도 보조)"

    # ---------------------------------------------------------
    # [추천 로직] DORMANT
    # ---------------------------------------------------------
    def _recommend_dormant(self, user_id: str, top_n=6):
        cands, _ = self._base_candidates()
        cands["diff_score"] = cands["difficulty"].apply(lambda x: 2.0 if x == "EASY" else 1.0)
        cands["norm_pop"] = self._safe_norm(np.log1p(cands["hit_num"]))
        cands["algo_score"] = cands["norm_pop"] * cands["diff_score"]
        return cands, "DORMANT: 입문용 EASY 우선(+인기도)"

    # ---------------------------------------------------------
    # [추천 로직] GUEST
    # ---------------------------------------------------------
    def _recommend_anonymous_topn(self, top_n=6):
        cands, _ = self._base_candidates()
        cands["log_cnt"] = cands["contest_pk"].astype(str).map(self.log_pop_by_contest).fillna(0.0)

        cands["norm_log"] = self._safe_norm(np.log1p(cands["log_cnt"]))
        cands["norm_pop"] = self._safe_norm(np.log1p(cands["hit_num"]))

        cands["algo_score"] = 0.7 * cands["norm_log"] + 0.3 * cands["norm_pop"]
        return cands, "GUEST: 실시간 인기(로그)+조회수"

    # ---------------------------------------------------------
    # [설명 컬럼] reason_tag / ai_summary / contrib_text / dominant_factor / score_formula
    # ---------------------------------------------------------
    def _add_explain_cols(self, df: pd.DataFrame, segment: str, user_id: str) -> pd.DataFrame:
        df = df.copy()

        # reason_tag 기본값
        if segment in ("POWER", "LIGHT"):
            df["reason_tag"] = "취향 저격"
        elif segment == "DORMANT":
            df["reason_tag"] = "입문 추천"
        else:
            df["reason_tag"] = "지금 인기"

        # ai_summary 작성용 키워드(관심사 매칭 1개 뽑기)
        intr_list = []
        if segment in ("POWER", "LIGHT"):
            u = self.users[self.users["member_pk"].astype(str) == str(user_id)]
            if not u.empty:
                intr_list = list(self._split_codes(u.iloc[0].get("CCF_interests", "")))

        def pick_match_keyword(row):
            if not intr_list:
                return None
            row_fields = self._split_codes(row.get("contest_field", ""))
            for k in intr_list:
                if k and k in row_fields:
                    return k
            return None

        # --- ai_summary ---
        if segment in ("POWER", "LIGHT"):
            kw = df.apply(pick_match_keyword, axis=1)
            df["ai_summary"] = np.where(
                kw.notna(),
                "'" + kw.astype(str) + "' 분야와 일치하며, 마감이 임박해 놓치면 아쉬운 공모전입니다.",
                "설정하신 관심사와 유사하며, 마감이 임박해 놓치면 아쉬운 공모전입니다.",
            )
        elif segment == "DORMANT":
            df["ai_summary"] = "부담 없이 시작하기 좋은 공모전입니다. EASY/입문형 유형을 우선 추천했습니다."
        else:
            df["ai_summary"] = "최근 사용자들이 많이 확인/지원하는 공모전입니다. 지금 뜨는 공모전부터 살펴보세요."

        # --- 기여도(contribution) 표시 ---
        # 원칙: '가중치 반영 기여도' = weight * normalized_component
        if segment == "POWER":
            # 기여도 계산
            ch = 1.5 * df.get("norm_history", 0.0)
            ci = 1.0 * df.get("norm_interest", 0.0)
            cp = 0.3 * df.get("norm_pop", 0.0)
            s = (ch + ci + cp).replace(0, np.nan)

            ph = (ch / s * 100).fillna(0.0)
            pi = (ci / s * 100).fillna(0.0)
            pp = (cp / s * 100).fillna(0.0)

            df["contrib_history_pct"] = ph.round(0)
            df["contrib_interest_pct"] = pi.round(0)
            df["contrib_pop_pct"] = pp.round(0)

            df["contrib_text"] = (
                "이력 " + df["contrib_history_pct"].astype(int).astype(str) + "% · "
                "관심 " + df["contrib_interest_pct"].astype(int).astype(str) + "% · "
                "인기 " + df["contrib_pop_pct"].astype(int).astype(str) + "%"
            )

            # dominant factor
            def dom(row):
                parts = {
                    "이력 기반": row.get("contrib_history_pct", 0),
                    "관심 기반": row.get("contrib_interest_pct", 0),
                    "인기 기반": row.get("contrib_pop_pct", 0),
                }
                return max(parts, key=parts.get)

            df["dominant_factor"] = df.apply(dom, axis=1)
            df["score_formula"] = df.apply(
                lambda r: f"1.5×이력({float(r.get('norm_history',0)):.2f}) + "
                          f"1.0×관심({float(r.get('norm_interest',0)):.2f}) + "
                          f"0.3×인기({float(r.get('norm_pop',0)):.2f})",
                axis=1,
            )

        elif segment == "LIGHT":
            ci = 1.0 * df.get("norm_interest", 0.0)
            cp = 0.3 * df.get("norm_pop", 0.0)
            s = (ci + cp).replace(0, np.nan)

            pi = (ci / s * 100).fillna(0.0)
            pp = (cp / s * 100).fillna(0.0)

            df["contrib_interest_pct"] = pi.round(0)
            df["contrib_pop_pct"] = pp.round(0)
            df["contrib_text"] = (
                "관심 " + df["contrib_interest_pct"].astype(int).astype(str) + "% · "
                "인기 " + df["contrib_pop_pct"].astype(int).astype(str) + "%"
            )
            df["dominant_factor"] = np.where(df["contrib_interest_pct"] >= df["contrib_pop_pct"], "관심 기반", "인기 기반")
            df["score_formula"] = df.apply(
                lambda r: f"관심({float(r.get('norm_interest',0)):.2f}) + 0.3×인기({float(r.get('norm_pop',0)):.2f})",
                axis=1,
            )

        elif segment == "GUEST":
            cl = 0.7 * df.get("norm_log", 0.0)
            cp = 0.3 * df.get("norm_pop", 0.0)
            s = (cl + cp).replace(0, np.nan)

            pl = (cl / s * 100).fillna(0.0)
            pp = (cp / s * 100).fillna(0.0)

            df["contrib_log_pct"] = pl.round(0)
            df["contrib_pop_pct"] = pp.round(0)
            df["contrib_text"] = (
                "로그 " + df["contrib_log_pct"].astype(int).astype(str) + "% · "
                "조회 " + df["contrib_pop_pct"].astype(int).astype(str) + "%"
            )
            df["dominant_factor"] = np.where(df["contrib_log_pct"] >= df["contrib_pop_pct"], "로그 기반", "조회 기반")
            df["score_formula"] = df.apply(
                lambda r: f"0.7×로그({float(r.get('norm_log',0)):.2f}) + 0.3×조회({float(r.get('norm_pop',0)):.2f})",
                axis=1,
            )

        else:  # DORMANT
            df["contrib_text"] = "인기 기반 + EASY 보정"
            df["dominant_factor"] = "입문형 우선"
            df["score_formula"] = df.apply(
                lambda r: f"인기({float(r.get('norm_pop',0)):.2f}) × 난이도({float(r.get('diff_score',1.0)):.1f})",
                axis=1,
            )

        return df

    # ---------------------------------------------------------
    # [최종 점수 환산] final_score = raw/theoretical_max * 100
    # ---------------------------------------------------------
    def _theoretical_max(self, segment: str) -> float:
        # norm_*는 최대 1.0을 가정
        if segment == "POWER":
            return 1.5 + 1.0 + 0.3  # 2.8
        if segment == "LIGHT":
            return 1.0 + 0.3        # 1.3
        if segment == "GUEST":
            return 0.7 + 0.3        # 1.0
        if segment == "DORMANT":
            # norm_pop 최대 1.0 * diff(EASY=2.0) 최대치
            return 2.0
        return 1.0

    # ---------------------------------------------------------
    # [메인] get_recommendations
    # ---------------------------------------------------------
    def get_recommendations(self, user_id: str, top_n=6):
        segment = self.identify_segment(user_id)

        if segment == "POWER":
            df, reason = self._recommend_power(user_id, top_n * 3)
        elif segment == "DORMANT":
            df, reason = self._recommend_dormant(user_id, top_n * 3)
        elif segment == "LIGHT":
            df, reason = self._recommend_light(user_id, top_n * 3)
        else:
            df, reason = self._recommend_anonymous_topn(top_n * 3)

        if df is None or df.empty:
            return df, segment, reason

        # 중복 제거(제목 기준)
        if "program_nm" in df.columns:
            df = df.drop_duplicates(subset=["program_nm"]).copy()

        # raw_score
        df["raw_score"] = df["algo_score"].astype(float)

        # final_score (납득 가능한 %)
        seg_max = self._theoretical_max(segment)
        if seg_max <= 0:
            seg_max = 1.0

        df["final_score"] = (df["raw_score"] / seg_max) * 100
        df["final_score"] = df["final_score"].clip(lower=0, upper=100)
        
        # [수정] 점수 산출 설명용 최대 점수 컬럼 추가
        df["seg_max_score"] = seg_max

        # 설명 컬럼들 추가
        df = self._add_explain_cols(df, segment, user_id)

        # 메타
        df["user_segment"] = segment
        df["recommend_reason"] = reason

        # 정렬/슬라이싱
        df = df.sort_values(by="final_score", ascending=False).head(top_n).copy()
        df["final_score"] = df["final_score"].round(0).astype(int)

        return df, segment, reason