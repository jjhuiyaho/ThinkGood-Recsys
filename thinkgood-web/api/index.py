from fastapi import FastAPI
import pandas as pd
import os
from recommender import Recommender

app = FastAPI()

# 파일 절대 경로 설정 (Vercel 환경 대응)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_NOW = pd.Timestamp("2023-02-11")

# 데이터 미리 로드 (서버 실행 시 1회만)
try:
    contest_df = pd.read_parquet(os.path.join(BASE_DIR, "Contest.parquet"))
    user_master = pd.read_parquet(os.path.join(BASE_DIR, "User_Master.parquet"))
    user_log = pd.read_parquet(os.path.join(BASE_DIR, "User_Activity_Log.parquet"))
    
    contest_df["contest_pk"] = contest_df["contest_pk"].astype(str)
    user_master["member_pk"] = user_master["member_pk"].astype(str)
    if "putup_edt" in contest_df.columns:
        contest_df["putup_edt"] = pd.to_datetime(contest_df["putup_edt"], errors="coerce")
        
    recommender = Recommender(user_master, user_log, contest_df, now_ts=SIM_NOW)
except Exception as e:
    recommender = None
    print(f"Data Load Error: {e}")

@app.get("/api/recommend/{user_id}")
def get_recommendation(user_id: str):
    if not recommender:
        return {"error": "엔진이 로드되지 않았습니다."}
    
    recs, segment, reason = recommender.get_recommendations(user_id, top_n=12)
    
    if recs is None or recs.empty:
        return {"user_id": user_id, "segment": segment, "recommendations": []}

    # DataFrame 내 NaN 값을 None으로 변환하여 JSON 직렬화 에러 방지
    recs = recs.fillna("")
    recs_json = recs.to_dict(orient="records")
    
    return {
        "user_id": user_id,
        "segment": segment,
        "reason": reason,
        "recommendations": recs_json
    }
