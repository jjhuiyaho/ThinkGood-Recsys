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
  const res = await fetch(`/api/recommend?user_id=${encodeURIComponent(userId)}&top_n=${topN}`);
  if (!res.ok) throw new Error("API 요청 실패");
  return res.json();
}

// --------------------------------------------------
// 카드
// --------------------------------------------------
function ContestCard({ item, debugMode, onOpen }: { item: Rec; debugMode: boolean; onOpen: () => void }) {
  let d = item.d_day;
  if (d === null || d === undefined || d === "") d = 999;
  d = Number(d);

  const dBadge =
    d >= 0 ? (
      <span className="badge-dday">D-{d}</span>
    ) : (
      <span className="badge-dday" style={{ background: "#666" }}>
        D+{Math.abs(d)}
      </span>
    );

  const rawCats = String(item["분야_한글"] || "");
  const cats = rawCats.split(",").map((c) => c.trim()).filter(Boolean);
  const catBadges =
    cats.length > 1 ? (
      <>
        <span className="badge-cate">{cats[0]}</span>
        <span className="badge-plus">+{cats.length - 1}</span>
      </>
    ) : cats.length === 1 ? (
      <span className="badge-cate">{cats[0]}</span>
    ) : (
      <span className="badge-cate">기타</span>
    );

  const score = Math.round(Number(item.final_score ?? item.total_score ?? 0));

  return (
    <div className="card-container">
      <div className="card-img-wrapper">
        {item.img_url_full ? (
          <img src={item.img_url_full} className="card-img" alt="poster" />
        ) : (
          <div style={{ color: "#AAA", fontSize: "0.85rem" }}>NO IMAGE</div>
        )}
      </div>
      <div className="card-content">
        <div style={{ marginBottom: 6 }}>
          {dBadge}
          {catBadges}
        </div>
        <div className="card-title">{item.program_nm || "제목 없음"}</div>
        <div className="user-reason">{item.reason_tag || "추천"}</div>
        <button onClick={onOpen} className="btn-outline" style={{ marginTop: 10, fontSize: "0.8rem" }}>
          상세보기
        </button>
      </div>
      {debugMode && (
        <div className="preview-bar">
          <span className="preview-label">종합 적합도</span>
          <span className="preview-score">{score}점</span>
        </div>
      )}
    </div>
  );
}

// --------------------------------------------------
// 상세 모달
// --------------------------------------------------
function DetailModal({ item, debugMode, onClose }: { item: Rec; debugMode: boolean; onClose: () => void }) {
  const sDate = String(item.putup_sdt || "").slice(0, 10);
  const eDate = String(item.putup_edt || "").slice(0, 10);
  const period = !eDate || eDate === "nan" ? "상시 모집" : `${sDate} ~ ${eDate}`;

  let dDay = item.d_day;
  dDay = dDay === null || dDay === undefined ? 999 : Number(dDay);
  let dBadgeText = "마감";
  let dColor = "#666";
  if (dDay > 0) { dBadgeText = `D-${dDay}`; dColor = "#D32F2F"; }
  else if (dDay === 0) { dBadgeText = "D-Day"; dColor = "#D32F2F"; }

  let field = item["분야_한글"] || "-";
  const subField = item["세부분야_한글"];
  if (subField) field += ` (${subField})`;

  let target = String(item["참가자격_한글"] || "").trim();
  if (!target || target === "nan" || target === "-") target = "제한 없음";
  else if (target.includes("제한 없음") || target.includes("제한없음")) target = "제한 없음";

  const prize = item.prize_money && String(item.prize_money).trim() ? item.prize_money : "-";
  const hitCnt = Number(item.hit || 0).toLocaleString();

  const rawScore = Number(item.raw_score ?? item.algo_score ?? 0);
  const finalScore = Math.round(Number(item.final_score ?? item.total_score ?? 0));
  const segMax = Number(item.seg_max_score ?? 1);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>

        <div className="title-area">
          <span
            style={{
              backgroundColor: dColor, color: "white", padding: "4px 8px",
              borderRadius: 4, fontSize: "0.8rem", fontWeight: "bold",
            }}
          >
            {dBadgeText}
          </span>
          <div className="main-title">{item.program_nm}</div>
          <div className="sub-info">
            <span>조회수 {hitCnt}회</span>
            <span>등록일 {sDate}</span>
          </div>
        </div>

        <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
          <div style={{ flex: "1 1 280px" }}>
            {item.img_url_full ? (
              <img src={item.img_url_full} style={{ width: "100%", borderRadius: 8, objectFit: "cover" }} alt="poster" />
            ) : (
              <div
                style={{
                  width: "100%", height: 320, background: "#F0F0F0", display: "flex",
                  alignItems: "center", justifyContent: "center", color: "#AAA", borderRadius: 8,
                }}
              >
                이미지 없음
              </div>
            )}
          </div>

          <div style={{ flex: "1.3 1 340px" }}>
            <table className="spec-table">
              <tbody>
                <tr><td className="spec-label">분야</td><td className="spec-value">{field}</td></tr>
                <tr><td className="spec-label">주최/주관</td><td className="spec-value">{item.host_display}</td></tr>
                <tr><td className="spec-label">참가자격</td><td className="spec-value">{target}</td></tr>
                <tr><td className="spec-label">접수기간</td><td className="spec-value">{period}</td></tr>
                <tr><td className="spec-label">시상내역</td><td className="spec-value">{prize}</td></tr>
              </tbody>
            </table>

            {item.hompage_url ? (
              <a
                href={item.hompage_url}
                target="_blank"
                rel="noreferrer"
                className="btn-primary"
                style={{ display: "block", textAlign: "center", textDecoration: "none" }}
              >
                홈페이지 바로가기
              </a>
            ) : (
              <button className="btn-secondary" disabled>홈페이지 정보 없음</button>
            )}

            <div style={{ marginTop: 20 }}>
              <div style={{ fontWeight: 700, marginBottom: 8 }}>🤖 AI 추천 분석</div>
              {(item.reason_tag || item.ai_summary) && (
                <div className="summary-box">
                  <span className="summary-badge">{item.reason_tag}</span>
                  <div className="summary-text">{item.ai_summary}</div>
                </div>
              )}

              {debugMode && (
                <div className="report-box">
                  <div className="report-title">AI 적합도 리포트</div>
                  {item.contrib_text && (
                    <div style={{ color: "#CFD8DC", fontSize: "0.85rem", marginBottom: 8 }}>{item.contrib_text}</div>
                  )}
                  {item.score_formula && (
                    <div style={{ color: "#90A4AE", fontSize: "0.8rem", marginBottom: 12 }}>{item.score_formula}</div>
                  )}
                  <div style={{
                    background: "rgba(0,0,0,0.2)", padding: 10, borderRadius: 6, display: "flex",
                    alignItems: "center", justifyContent: "center", gap: 10, flexWrap: "wrap",
                  }}>
                    <span style={{ fontWeight: 700 }}>{rawScore.toFixed(2)}</span>
                    <span style={{ color: "#90A4AE" }}>÷</span>
                    <span style={{ color: "#B0BEC5" }}>{segMax.toFixed(1)} (Max)</span>
                    <span style={{ color: "#90A4AE" }}>× 100 =</span>
                    <span className="report-total-score">{finalScore}점</span>
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
// 사이드바
// --------------------------------------------------
function Sidebar({
  data, debugMode, setDebugMode, onDemoLogin,
}: {
  data: ApiResponse | null;
  debugMode: boolean;
  setDebugMode: (v: boolean) => void;
  onDemoLogin: (uid: string) => void;
}) {
  return (
    <aside style={{ width: 280, flexShrink: 0 }}>
      <div className="profile-box" style={{ marginBottom: 16 }}>
        <div style={{ fontWeight: 800, marginBottom: 10 }}>관리자 메뉴</div>
        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.9rem", cursor: "pointer" }}>
          <input type="checkbox" checked={debugMode} onChange={(e) => setDebugMode(e.target.checked)} />
          분석 모드
        </label>
      </div>

      <div className="profile-box" style={{ marginBottom: 16 }}>
        <div style={{ fontWeight: 800, marginBottom: 10 }}>시연 계정 접속</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {DEMO_ACCOUNTS.map((acc) => (
            <button key={acc.user_id} className="btn-outline" onClick={() => onDemoLogin(acc.user_id)}>
              {acc.label}
            </button>
          ))}
        </div>
      </div>

      {data && (
        <div className="profile-box">
          <div style={{ fontWeight: 800, marginBottom: 8 }}>내 프로필</div>
          <div className="profile-row"><div className="profile-label">ID</div><div className="profile-val">{data.user_id}</div></div>
          <div className="profile-row">
            <div className="profile-label">유형</div>
            <div className="profile-val" style={{ color: "#D32F2F", fontWeight: 700 }}>{data.segment_display}</div>
          </div>
          {data.profile && (
            <>
              <div className="profile-row">
                <div className="profile-label">활동</div>
                <div className="profile-val">
                  <div style={{ fontWeight: 700 }}>총 {data.profile.apply_cnt}회 지원</div>
                  <div style={{ fontSize: "0.8rem", color: "#666" }}>{data.profile.apply_info_txt}</div>
                </div>
              </div>
              <div className="profile-row">
                <div className="profile-label">관심사</div>
                <div className="profile-val" style={{ fontSize: "0.85rem" }}>{data.profile.interest_txt}</div>
              </div>
            </>
          )}
          <hr style={{ margin: "10px 0", border: 0, borderTop: "1px dashed #DDD" }} />
          <div style={{ fontWeight: 700, fontSize: "0.85rem" }}>적용 알고리즘</div>
          <div style={{ background: "#F8F9FA", padding: 8, borderRadius: 4, fontSize: "0.8rem", marginTop: 5 }}>
            {data.strategy.method}
          </div>
          <div style={{ marginTop: 10, fontWeight: 700, fontSize: "0.85rem" }}>로직 설명</div>
          <div style={{ background: "#F8F9FA", padding: 8, borderRadius: 4, fontSize: "0.8rem", marginTop: 5, lineHeight: 1.4 }}>
            {data.strategy.desc}
          </div>
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
  const [debugMode, setDebugMode] = useState(false);
  const [category, setCategory] = useState("전체");
  const [selectedItem, setSelectedItem] = useState<Rec | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 최초 로드: GUEST 추천 (비로그인 기본 화면 + 사이드바 전략 정보)
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

  const doLogin = async (uid: string) => {
    if (!uid.startsWith("M")) {
      alert("잘못된 아이디 형식입니다. 'M'으로 시작하는 아이디를 입력해주세요.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const json = await fetchRecommend(uid, 12);
      if (json.error) {
        setError(json.error);
      } else {
        setData(json);
        setIsLoggedIn(true);
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
  const filteredGuestRecs =
    category === "전체"
      ? guestRecs
      : (() => {
          const f = guestRecs.filter((r) => String(r["분야_한글"] || "").includes(category));
          return f.length < 4 ? guestRecs : f;
        })();

  return (
    <div style={{ minHeight: "100vh", padding: 24 }}>
      <div style={{ maxWidth: 1200, margin: "0 auto", display: "flex", gap: 24, alignItems: "flex-start" }}>
        <Sidebar data={data} debugMode={debugMode} setDebugMode={setDebugMode} onDemoLogin={doLogin} />

        <main style={{ flex: 1, minWidth: 0 }}>
          {error && (
            <div style={{ background: "#FDECEA", color: "#B71C1C", padding: 12, borderRadius: 6, marginBottom: 16, fontSize: "0.9rem" }}>
              {error}
            </div>
          )}

          {!isLoggedIn ? (
            <>
              <div className="login-container" style={{ marginBottom: 32 }}>
                <div className="login-title">누구나 도전을 꿈꾸고 경험하도록</div>
                <div className="login-subtitle">오늘 더 나은 세상을 만들어 갑니다.</div>
                <input
                  type="text"
                  placeholder="M24_..."
                  value={userIdInput}
                  onChange={(e) => setUserIdInput(e.target.value)}
                  style={{ width: "100%", border: "1px solid #ccc", padding: 12, borderRadius: 6, marginBottom: 12 }}
                />
                <button className="btn-primary" disabled={loading} onClick={() => doLogin(userIdInput.trim())}>
                  {loading ? "로딩중..." : "시작하기"}
                </button>
              </div>

              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 20 }}>
                {CATEGORIES.map((c) => (
                  <button
                    key={c}
                    className={`btn-outline ${category === c ? "active" : ""}`}
                    onClick={() => setCategory(c)}
                  >
                    {c}
                  </button>
                ))}
              </div>

              <h3 style={{ fontWeight: 800, fontSize: "1.15rem", marginBottom: 16 }}>{category} 인기 공모전</h3>
              {loading ? (
                <p>불러오는 중...</p>
              ) : filteredGuestRecs.length ? (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 20 }}>
                  {filteredGuestRecs.slice(0, 8).map((item, idx) => (
                    <ContestCard key={idx} item={item} debugMode={debugMode} onOpen={() => setSelectedItem(item)} />
                  ))}
                </div>
              ) : (
                <p>추천 결과가 없습니다.</p>
              )}
            </>
          ) : (
            <>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24, paddingBottom: 16, borderBottom: "1px solid #e5e5e5" }}>
                <h2 style={{ fontWeight: 800, fontSize: "1.4rem" }}>안녕하세요, {data?.user_id}님!</h2>
                <button className="btn-secondary" style={{ width: "auto", padding: "8px 16px" }} onClick={handleLogout}>
                  Logout
                </button>
              </div>

              {loading ? (
                <p>불러오는 중...</p>
              ) : data && data.recommendations.length ? (
                <>
                  <h3 style={{ fontWeight: 800, marginBottom: 16 }}>오늘의 맞춤 추천</h3>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 20, marginBottom: 32 }}>
                    {data.recommendations.slice(0, 4).map((item, idx) => (
                      <ContestCard key={idx} item={item} debugMode={debugMode} onOpen={() => setSelectedItem(item)} />
                    ))}
                  </div>

                  {data.recommendations.length > 4 && (
                    <>
                      <h3 style={{ fontWeight: 800, marginBottom: 16 }}>놓치면 아쉬운 발견</h3>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 20 }}>
                        {data.recommendations.slice(4).map((item, idx) => (
                          <ContestCard key={idx} item={item} debugMode={debugMode} onOpen={() => setSelectedItem(item)} />
                        ))}
                      </div>
                    </>
                  )}
                </>
              ) : (
                <p>추천 결과가 없습니다.</p>
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
