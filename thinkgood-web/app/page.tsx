"use client";

import { useEffect, useState } from "react";

type Rec = Record<string, any>;

type ApiResponse = {
  user_id: string;
  segment: string;
  segment_display: string;
  reason: string;
  strategy: { method: string; desc: string };
  profile: { interest_txt: string; apply_cnt: number; apply_info_txt: string } | null;
  recommendations: Rec[];
  error?: string;
};

const DEMO_ACCOUNTS = [
  { label: "파워회원(1)", user_id: "M22_02522" },
  { label: "파워회원(2)", user_id: "M15_01349" },
  { label: "파워회원(3)", user_id: "M22_07072" },
  { label: "라이트회원(1)", user_id: "M22_05203" },
  { label: "라이트회원(2)", user_id: "M21_01623" },
  { label: "휴면회원", user_id: "M10_00108" },
];

const CATEGORIES = [
  "전체", "기획/아이디어", "광고/마케팅", "논문/리포트", "영상/UCC/사진",
  "디자인/캐릭터/웹툰", "IT/소프트웨어", "과학/공학", "문학/수기",
  "건축/인테리어", "취업/창업",
];

async function fetchRecommend(userId: string, topN: number): Promise<ApiResponse> {
  const res = await fetch(`https://thinkgood-recsys.onrender.com/api/recommend?user_id=${userId}&top_n=${topN}`);
  if (!res.ok) throw new Error("API 요청 실패");
  return res.json();
}

// --------------------------------------------------
// 카드 컴포넌트
// --------------------------------------------------
function ContestCard({ item, debugMode, onOpen }: { item: Rec; debugMode: boolean; onOpen: () => void }) {
  let d = item.d_day;
  const isAlwaysOpen = d === null || d === undefined || d === "" || d === 999;
  
  const dBadge = isAlwaysOpen ? (
    <span style={{ background: "#4CAF50", color: "#fff", padding: "3px 6px", borderRadius: 4, fontSize: "0.75rem", fontWeight: "bold", marginRight: 6 }}>상시모집</span>
  ) : Number(d) >= 0 ? (
    <span style={{ background: "#D32F2F", color: "#fff", padding: "3px 6px", borderRadius: 4, fontSize: "0.75rem", fontWeight: "bold", marginRight: 6 }}>D-{d}</span>
  ) : (
    <span style={{ background: "#666", color: "#fff", padding: "3px 6px", borderRadius: 4, fontSize: "0.75rem", fontWeight: "bold", marginRight: 6 }}>마감</span>
  );

  const rawCats = String(item["분야_한글"] || "");
  const cats = rawCats.split(",").map((c) => c.trim()).filter(Boolean);
  const catBadges = cats.length > 1 ? (
    <span style={{ fontSize: "0.75rem", color: "#555" }}>{cats[0]} +{cats.length - 1}</span>
  ) : cats.length === 1 ? (
    <span style={{ fontSize: "0.75rem", color: "#555" }}>{cats[0]}</span>
  ) : (
    <span style={{ fontSize: "0.75rem", color: "#555" }}>기타</span>
  );

  const score = Math.round(Number(item.final_score ?? item.total_score ?? 0));

  return (
    <div style={{ border: "1px solid #eee", borderRadius: 8, overflow: "hidden", cursor: "pointer", transition: "transform 0.2s", background: "#fff", display: "flex", flexDirection: "column", height: "100%" }} onClick={onOpen}>
      <div style={{ width: "100%", height: 160, background: "#f5f5f5", display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
        {item.img_url_full ? (
          <img src={item.img_url_full} style={{ width: "100%", height: "100%", objectFit: "cover" }} alt="poster" />
        ) : (
          <div style={{ color: "#AAA", fontSize: "0.85rem" }}>NO IMAGE</div>
        )}
      </div>
      <div style={{ padding: 16, flex: 1, display: "flex", flexDirection: "column" }}>
        <div style={{ marginBottom: 8 }}>{dBadge} {catBadges}</div>
        <div style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 8, lineHeight: 1.4, flex: 1 }}>{item.program_nm || "제목 없음"}</div>
        <div style={{ color: "#1976D2", fontSize: "0.85rem", fontWeight: 600, marginBottom: 12 }}>{item.reason_tag || "추천"}</div>
        
        {/* 분석 모드 켜졌을 때 카드 뷰어 */}
        {debugMode && (
          <div style={{ background: "#F4F6F8", padding: 10, borderRadius: 6, marginTop: "auto" }}>
            <div style={{ fontSize: "0.75rem", color: "#455A64", fontWeight: 700, marginBottom: 4 }}>📊 적합도: {score}점</div>
            <div style={{ fontSize: "0.7rem", color: "#607D8B", lineHeight: 1.3 }}>{item.contrib_text || "세부 지표 없음"}</div>
            {item.dominant_factor && <div style={{ fontSize: "0.7rem", color: "#D32F2F", marginTop: 4, fontWeight: "bold" }}>Core: {item.dominant_factor}</div>}
          </div>
        )}
      </div>
    </div>
  );
}

// --------------------------------------------------
// 상세 모달 컴포넌트
// --------------------------------------------------
function DetailModal({ item, debugMode, onClose }: { item: Rec; debugMode: boolean; onClose: () => void }) {
  const sDate = String(item.putup_sdt || "").slice(0, 10);
  const eDate = String(item.putup_edt || "").slice(0, 10);
  const period = !eDate || eDate === "nan" ? "상시 모집" : `${sDate} ~ ${eDate}`;

  let dDay = item.d_day;
  const isAlwaysOpen = dDay === null || dDay === undefined || dDay === "" || dDay === 999;
  
  let dBadgeText = isAlwaysOpen ? "상시모집" : Number(dDay) > 0 ? `D-${dDay}` : Number(dDay) === 0 ? "D-Day" : "마감";
  let dColor = isAlwaysOpen ? "#4CAF50" : Number(dDay) >= 0 ? "#D32F2F" : "#666";

  let field = item["분야_한글"] || "-";
  const subField = item["세부분야_한글"];
  if (subField) field += ` (${subField})`;

  let target = String(item["참가자격_한글"] || "").trim();
  if (!target || target === "nan" || target === "-") target = "제한 없음";

  const prize = item.prize_money && String(item.prize_money).trim() ? item.prize_money : "-";
  const hitCnt = Number(item.hit || 0).toLocaleString();

  const rawScore = Number(item.raw_score ?? item.algo_score ?? 0);
  const finalScore = Math.round(Number(item.final_score ?? item.total_score ?? 0));
  const segMax = Number(item.seg_max_score ?? 1);

  return (
    <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.6)", zIndex: 9999, display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }} onClick={onClose}>
      <div style={{ background: "#fff", width: "100%", maxWidth: 800, maxHeight: "90vh", borderRadius: 12, overflowY: "auto", position: "relative", padding: 30 }} onClick={(e) => e.stopPropagation()}>
        <button style={{ position: "absolute", top: 20, right: 20, background: "none", border: "none", fontSize: "1.5rem", cursor: "pointer" }} onClick={onClose}>×</button>

        <div style={{ marginBottom: 24, paddingBottom: 16, borderBottom: "1px solid #eee" }}>
          <span style={{ backgroundColor: dColor, color: "white", padding: "4px 8px", borderRadius: 4, fontSize: "0.8rem", fontWeight: "bold", marginRight: 10 }}>{dBadgeText}</span>
          <h2 style={{ fontSize: "1.4rem", fontWeight: 800, marginTop: 12, marginBottom: 8, lineHeight: 1.4 }}>{item.program_nm}</h2>
          <div style={{ fontSize: "0.85rem", color: "#666", display: "flex", gap: 12 }}>
            <span>조회수 {hitCnt}회</span>
            <span>등록일 {sDate !== "nan" ? sDate : "-"}</span>
          </div>
        </div>

        <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
          <div style={{ flex: "1 1 280px" }}>
            {item.img_url_full ? (
              <img src={item.img_url_full} style={{ width: "100%", borderRadius: 8, border: "1px solid #eee" }} alt="poster" />
            ) : (
              <div style={{ width: "100%", height: 320, background: "#F0F0F0", display: "flex", alignItems: "center", justifyContent: "center", color: "#AAA", borderRadius: 8 }}>이미지 없음</div>
            )}
          </div>

          <div style={{ flex: "1.3 1 340px" }}>
            <table style={{ width: "100%", fontSize: "0.9rem", borderCollapse: "collapse", marginBottom: 24 }}>
              <tbody>
                <tr style={{ borderBottom: "1px solid #eee" }}><td style={{ padding: "12px 0", width: "80px", color: "#666", fontWeight: "bold" }}>분야</td><td style={{ padding: "12px 0", color: "#222" }}>{field}</td></tr>
                <tr style={{ borderBottom: "1px solid #eee" }}><td style={{ padding: "12px 0", color: "#666", fontWeight: "bold" }}>주최/주관</td><td style={{ padding: "12px 0", color: "#222" }}>{item.host_display}</td></tr>
                <tr style={{ borderBottom: "1px solid #eee" }}><td style={{ padding: "12px 0", color: "#666", fontWeight: "bold" }}>참가자격</td><td style={{ padding: "12px 0", color: "#222" }}>{target}</td></tr>
                <tr style={{ borderBottom: "1px solid #eee" }}><td style={{ padding: "12px 0", color: "#666", fontWeight: "bold" }}>접수기간</td><td style={{ padding: "12px 0", color: "#222" }}>{period}</td></tr>
                <tr><td style={{ padding: "12px 0", color: "#666", fontWeight: "bold" }}>시상내역</td><td style={{ padding: "12px 0", color: "#222" }}>{prize}</td></tr>
              </tbody>
            </table>

            {item.hompage_url && item.hompage_url !== "nan" ? (
              <a href={item.hompage_url} target="_blank" rel="noreferrer" style={{ display: "block", textAlign: "center", background: "#111", color: "#fff", padding: "12px", borderRadius: 6, textDecoration: "none", fontWeight: "bold" }}>홈페이지 바로가기</a>
            ) : (
              <button style={{ width: "100%", padding: "12px", background: "#e0e0e0", color: "#888", border: "none", borderRadius: 6, fontWeight: "bold" }} disabled>홈페이지 정보 없음</button>
            )}

            <div style={{ marginTop: 24 }}>
              <div style={{ fontWeight: 800, marginBottom: 12, fontSize: "1.1rem" }}>🤖 AI 추천 분석</div>
              {(item.reason_tag || item.ai_summary) && (
                <div style={{ background: "#E3F2FD", padding: 16, borderRadius: 8, marginBottom: 16 }}>
                  <span style={{ display: "inline-block", background: "#1976D2", color: "#fff", padding: "2px 8px", borderRadius: 4, fontSize: "0.75rem", fontWeight: "bold", marginBottom: 8 }}>{item.reason_tag}</span>
                  <div style={{ fontSize: "0.9rem", color: "#0D47A1", lineHeight: 1.5 }}>{item.ai_summary}</div>
                </div>
              )}

              {/* 디버그 모드(XAI) 리포트 UI 복구 */}
              {debugMode && (
                <div style={{ background: "#263238", padding: 16, borderRadius: 8, color: "#fff" }}>
                  <div style={{ fontWeight: "bold", marginBottom: 12, color: "#80CBC4" }}>[분석 모드] 세그먼트 스코어링 리포트</div>
                  {item.contrib_text && (
                    <div style={{ fontSize: "0.85rem", color: "#CFD8DC", marginBottom: 8 }}>✔ 기여도: {item.contrib_text}</div>
                  )}
                  {item.score_formula && (
                    <div style={{ fontSize: "0.8rem", color: "#90A4AE", marginBottom: 16, background: "rgba(255,255,255,0.05)", padding: 8, borderRadius: 4 }}>
                      f(x) = {item.score_formula}
                    </div>
                  )}
                  <div style={{ background: "rgba(0,0,0,0.3)", padding: 12, borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", gap: 12, flexWrap: "wrap", fontSize: "0.9rem" }}>
                    <span>원점수 <b>{rawScore.toFixed(2)}</b></span>
                    <span style={{ color: "#90A4AE" }}>/</span>
                    <span style={{ color: "#90A4AE" }}>최대 <b>{segMax.toFixed(1)}</b></span>
                    <span style={{ color: "#90A4AE" }}>=</span>
                    <span style={{ fontSize: "1.1rem", fontWeight: 800, color: "#FFCA28" }}>적합도 {finalScore}점</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// --------------------------------------------------
// 사이드바 컴포넌트
// --------------------------------------------------
function Sidebar({
  data, debugMode, setDebugMode, topN, setTopN, onDemoLogin,
}: {
  data: ApiResponse | null;
  debugMode: boolean;
  setDebugMode: (v: boolean) => void;
  topN: number;
  setTopN: (n: number) => void;
  onDemoLogin: (uid: string, top_n: number) => void;
}) {
  return (
    <aside style={{ width: 280, flexShrink: 0 }}>
      {/* 관리자 메뉴 (Streamlit 사이드바 복구) */}
      <div style={{ background: "#fff", padding: 20, borderRadius: 8, border: "1px solid #eaeaea", marginBottom: 20 }}>
        <div style={{ fontWeight: 800, fontSize: "1.1rem", marginBottom: 16 }}>🛠️ 관리자 설정</div>
        
        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.95rem", cursor: "pointer", marginBottom: 20, background: "#f8f9fa", padding: "10px", borderRadius: 6, fontWeight: "bold" }}>
          <input type="checkbox" checked={debugMode} onChange={(e) => setDebugMode(e.target.checked)} style={{ transform: "scale(1.2)" }} />
          분석 모드 (XAI) 켜기
        </label>

        <div style={{ marginBottom: 10, fontSize: "0.9rem", fontWeight: "bold", color: "#555" }}>추천 공모전 개수: {topN}개</div>
        <input 
          type="range" 
          min="4" max="30" step="2" 
          value={topN} 
          onChange={(e) => {
            setTopN(Number(e.target.value));
            if(data?.user_id) onDemoLogin(data.user_id, Number(e.target.value));
          }}
          style={{ width: "100%", marginBottom: 10 }}
        />
        <div style={{ fontSize: "0.75rem", color: "#888", marginBottom: 20 }}>게이지를 움직이면 즉시 재조회됩니다.</div>
      </div>

      <div style={{ background: "#fff", padding: 20, borderRadius: 8, border: "1px solid #eaeaea", marginBottom: 20 }}>
        <div style={{ fontWeight: 800, marginBottom: 12 }}>시연 계정 접속</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {DEMO_ACCOUNTS.map((acc) => (
            <button key={acc.user_id} onClick={() => onDemoLogin(acc.user_id, topN)} style={{ padding: "8px 12px", background: "#f1f3f5", border: "none", borderRadius: 6, cursor: "pointer", textAlign: "left", fontSize: "0.9rem", color: "#333", transition: "background 0.2s" }} onMouseOver={(e) => e.currentTarget.style.background = "#e9ecef"} onMouseOut={(e) => e.currentTarget.style.background = "#f1f3f5"}>
              {acc.label} <span style={{ color: "#aaa", fontSize: "0.75rem", marginLeft: 4 }}>{acc.user_id}</span>
            </button>
          ))}
        </div>
      </div>

      {data && data.user_id !== "GUEST" && (
        <div style={{ background: "#fff", padding: 20, borderRadius: 8, border: "1px solid #eaeaea" }}>
          <div style={{ fontWeight: 800, marginBottom: 16 }}>내 프로필</div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, fontSize: "0.9rem" }}><span style={{ color: "#666" }}>ID</span><span style={{ fontWeight: "bold" }}>{data.user_id}</span></div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, fontSize: "0.9rem" }}>
            <span style={{ color: "#666" }}>유형</span>
            <span style={{ color: "#D32F2F", fontWeight: 800 }}>{data.segment_display}</span>
          </div>
          {data.profile && (
            <>
              <div style={{ marginTop: 16, marginBottom: 4, fontSize: "0.85rem", color: "#666" }}>활동 내역</div>
              <div style={{ fontSize: "0.9rem", fontWeight: "bold", background: "#f8f9fa", padding: 8, borderRadius: 4 }}>총 {data.profile.apply_cnt}회 지원<br/><span style={{ fontSize: "0.75rem", color: "#555", fontWeight: "normal" }}>{data.profile.apply_info_txt}</span></div>
              
              <div style={{ marginTop: 12, marginBottom: 4, fontSize: "0.85rem", color: "#666" }}>관심사</div>
              <div style={{ fontSize: "0.85rem", background: "#f8f9fa", padding: 8, borderRadius: 4 }}>{data.profile.interest_txt}</div>
            </>
          )}
          <hr style={{ margin: "20px 0", border: 0, borderTop: "1px dashed #DDD" }} />
          <div style={{ fontWeight: 700, fontSize: "0.85rem", color: "#1976D2" }}>적용 알고리즘</div>
          <div style={{ background: "#E3F2FD", color: "#0D47A1", padding: 8, borderRadius: 4, fontSize: "0.8rem", marginTop: 5, fontWeight: "bold" }}>{data.strategy.method}</div>
          <div style={{ marginTop: 10, fontWeight: 700, fontSize: "0.85rem" }}>로직 설명</div>
          <div style={{ background: "#F8F9FA", padding: 8, borderRadius: 4, fontSize: "0.75rem", marginTop: 5, lineHeight: 1.5, color: "#555" }}>{data.strategy.desc}</div>
        </div>
      )}
    </aside>
  );
}

// --------------------------------------------------
// 메인 페이지
// --------------------------------------------------
export default function Home() {
  const [userIdInput, setUserIdInput] = useState("");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ApiResponse | null>(null);
  
  // 관리자 모드 상태
  const [debugMode, setDebugMode] = useState(false);
  const [topN, setTopN] = useState(12);

  const [category, setCategory] = useState("전체");
  const [selectedItem, setSelectedItem] = useState<Rec | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 최초 로드: GUEST 추천
  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const json = await fetchRecommend("GUEST", 30);
        if (json.error) setError(json.error);
        setData(json);
      } catch {
        setError("데이터를 불러오는데 실패했습니다.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const doLogin = async (uid: string, fetchTopN: number = topN) => {
    if (!uid.startsWith("M")) {
      alert("잘못된 아이디 형식입니다. 'M'으로 시작하는 아이디를 입력해주세요.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const json = await fetchRecommend(uid, fetchTopN);
      if (json.error) {
        setError(json.error);
      } else {
        setData(json);
        setIsLoggedIn(true);
        setUserIdInput(uid);
      }
    } catch {
      setError("데이터를 불러오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    setIsLoggedIn(false);
    setUserIdInput("");
    setLoading(true);
    try {
      const json = await fetchRecommend("GUEST", 30);
      setData(json);
    } finally {
      setLoading(false);
    }
  };

  const guestRecs = data?.recommendations || [];
  const filteredGuestRecs = category === "전체" ? guestRecs : (() => {
    const f = guestRecs.filter((r) => String(r["분야_한글"] || "").includes(category));
    return f.length < 4 ? guestRecs : f;
  })();

  return (
    <div style={{ minHeight: "100vh", padding: "40px 20px", background: "#fdfdfd" }}>
      <div style={{ maxWidth: 1300, margin: "0 auto", display: "flex", gap: 30, alignItems: "flex-start" }}>
        
        <Sidebar data={data} debugMode={debugMode} setDebugMode={setDebugMode} topN={topN} setTopN={setTopN} onDemoLogin={doLogin} />

        <main style={{ flex: 1, minWidth: 0 }}>
          {error && (
            <div style={{ background: "#FDECEA", color: "#B71C1C", padding: 16, borderRadius: 8, marginBottom: 20, fontWeight: "bold" }}>🚨 {error}</div>
          )}

          {!isLoggedIn ? (
            <>
              <div style={{ background: "#fff", padding: 40, borderRadius: 12, border: "1px solid #eaeaea", marginBottom: 40, textAlign: "center" }}>
                <h1 style={{ fontSize: "2rem", fontWeight: 900, marginBottom: 12, color: "#111" }}>누구나 도전을 꿈꾸고 경험하도록</h1>
                <p style={{ fontSize: "1.1rem", color: "#666", marginBottom: 30 }}>오늘 더 나은 세상을 만들어 갑니다.</p>
                <div style={{ maxWidth: 400, margin: "0 auto", display: "flex", gap: 10 }}>
                  <input
                    type="text"
                    placeholder="아이디 입력 (예: M24_...)"
                    value={userIdInput}
                    onChange={(e) => setUserIdInput(e.target.value)}
                    style={{ flex: 1, padding: "12px 16px", borderRadius: 8, border: "1px solid #ccc", fontSize: "1rem" }}
                  />
                  <button onClick={() => doLogin(userIdInput.trim(), topN)} disabled={loading} style={{ background: "#111", color: "#fff", border: "none", padding: "0 24px", borderRadius: 8, fontWeight: "bold", cursor: "pointer" }}>
                    {loading ? "조회중" : "시작하기"}
                  </button>
                </div>
              </div>

              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 24 }}>
                {CATEGORIES.map((c) => (
                  <button key={c} onClick={() => setCategory(c)} style={{ padding: "8px 16px", borderRadius: 20, border: category === c ? "none" : "1px solid #ddd", background: category === c ? "#111" : "#fff", color: category === c ? "#fff" : "#555", cursor: "pointer", fontWeight: category === c ? "bold" : "normal" }}>
                    {c}
                  </button>
                ))}
              </div>

              <h3 style={{ fontWeight: 800, fontSize: "1.4rem", marginBottom: 20 }}>🔥 {category} 인기 공모전</h3>
              {loading ? (
                <p style={{ color: "#888" }}>데이터를 분석 중입니다...</p>
              ) : filteredGuestRecs.length ? (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 24 }}>
                  {filteredGuestRecs.slice(0, 8).map((item, idx) => (
                    <ContestCard key={idx} item={item} debugMode={debugMode} onOpen={() => setSelectedItem(item)} />
                  ))}
                </div>
              ) : (
                <p style={{ color: "#888" }}>추천 결과가 없습니다.</p>
              )}
            </>
          ) : (
            <>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 30, paddingBottom: 20, borderBottom: "2px solid #111" }}>
                <h2 style={{ fontWeight: 900, fontSize: "1.8rem", color: "#111" }}>안녕하세요, <span style={{ color: "#1976D2" }}>{data?.user_id}</span>님!</h2>
                <button onClick={handleLogout} style={{ padding: "8px 16px", border: "1px solid #ccc", background: "#fff", borderRadius: 6, cursor: "pointer", fontWeight: "bold", color: "#555" }}>로그아웃</button>
              </div>

              {loading ? (
                <p style={{ color: "#888", fontSize: "1.1rem" }}>데이터를 분석 중입니다...</p>
              ) : data && data.recommendations.length ? (
                <>
                  <h3 style={{ fontWeight: 800, fontSize: "1.4rem", marginBottom: 20 }}>✨ 오늘의 맞춤 추천</h3>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 24, marginBottom: 40 }}>
                    {data.recommendations.slice(0, 4).map((item, idx) => (
                      <ContestCard key={idx} item={item} debugMode={debugMode} onOpen={() => setSelectedItem(item)} />
                    ))}
                  </div>

                  {data.recommendations.length > 4 && (
                    <>
                      <h3 style={{ fontWeight: 800, fontSize: "1.4rem", marginBottom: 20 }}>💡 놓치면 아쉬운 발견</h3>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 24 }}>
                        {data.recommendations.slice(4).map((item, idx) => (
                          <ContestCard key={idx} item={item} debugMode={debugMode} onOpen={() => setSelectedItem(item)} />
                        ))}
                      </div>
                    </>
                  )}
                </>
              ) : (
                <p style={{ color: "#888" }}>추천 결과가 없습니다.</p>
              )}
            </>
          )}
        </main>
      </div>

      {selectedItem && (
        <DetailModal item={selectedItem} debugMode={debugMode} onClose={() => setSelectedItem(null)} />
      )}
    </div>
  );
}
