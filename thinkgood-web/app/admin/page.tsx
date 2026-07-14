"use client";

import { useState, useMemo } from "react";
import Link from "next/link";

// --------------------------------------------------
// 1. Constants (admin/constants.py 역할)
// --------------------------------------------------
const REGIONS = ["강원도", "경기도", "경상남도", "경상북도", "광주광역시", "대구광역시", "대전광역시", "부산광역시", "서울특별시", "세종특별자치시", "울산광역시", "인천광역시", "전라남도", "전라북도", "제주특별자치도", "충청남도", "충청북도"];
const STATUS_OPTIONS = ["게시", "비게시"];
const HOST_ORG_TYPES = ["중앙정부/기관", "공기업", "대기업", "신문/방송/언론", "외국계기업", "지방자치단체", "학교/재단/협회", "중소/벤처기업", "학회/비영리단체", "해외", "대행사", "진흥원/공공기관", "기타"];
const CONTEST_FIELDS = ["건축", "게임/소프트웨어", "과학", "광고/마케팅", "기획/아이디어", "네이밍/슬로건", "논문", "디자인", "만화/캐릭터", "문학/수기", "미술", "사진", "영상/UCC", "음악", "이벤트", "취업/창업", "해외"];
const KEYWORD_TAGS = ["환경", "경제", "기획", "정책", "교육", "IT/AI", "디자인", "문화", "사회", "헬스케어", "금융", "창업"];
const APPLY_METHOD_TYPES = ["홈페이지", "이메일", "방문", "우편", "기타"];

// --------------------------------------------------
// 2. Parsers (admin/eligibility_parser.py 역할)
// --------------------------------------------------
function parseEligibility(text: string) {
  if (!text || !text.trim()) return { ageMin: null, ageMax: null, conditionType: "none", keywordHit: null };
  const t = text.replace(/\s/g, "");

  // 1) 범위: 19세~39세
  let m = t.match(/(\d{1,2})세?[~\-](\d{1,2})세?/);
  if (m) return { ageMin: Math.min(Number(m[1]), Number(m[2])), ageMax: Math.max(Number(m[1]), Number(m[2])), conditionType: "range", keywordHit: null };

  // 2) 이상: 19세이상
  m = t.match(/(?:만)?(\d{1,2})세?(?:이상|부터)/);
  if (m) return { ageMin: Number(m[1]), ageMax: null, conditionType: "min", keywordHit: null };

  // 3) 이하: 40세이하
  m = t.match(/(\d{1,2})세?(?:이하|까지)/);
  if (m) return { ageMin: null, ageMax: Number(m[1]), conditionType: "max", keywordHit: null };

  // 4) 키워드
  const keywordMap: Record<string, string> = { "청소년": "청소년", "중학생": "중학생", "고등학생": "고등학생", "대학생": "대학생", "대학원생": "대학원생", "일반인": "일반인", "누구나": "누구나", "전국민": "전국민" };
  for (const [k, v] of Object.entries(keywordMap)) {
    if (t.includes(k)) return { ageMin: null, ageMax: null, conditionType: "keyword", keywordHit: v };
  }

  return { ageMin: null, ageMax: null, conditionType: "none", keywordHit: null };
}

// --------------------------------------------------
// 3. Keyword Extractor (admin/keyword_extractor.py 역할)
// --------------------------------------------------
const STOPWORDS = new Set(["및", "등", "수", "것", "이", "가", "을", "를", "은", "는", "에", "의", "와", "과", "로", "으로", "대상", "참여", "가능", "제출", "방법", "일정", "문의", "관련", "사항", "안내", "선정", "지원", "the", "and", "or", "to", "in", "for", "on", "with", "a", "an"]);
function extractKeywords(text: string, topK: number = 8) {
  if (!text) return [];
  const matches = text.match(/[가-힣A-Za-z0-9]{2,}/g) || [];
  const tokens = matches.map((t) => t.toLowerCase()).filter((t) => !STOPWORDS.has(t));
  
  const counts: Record<string, number> = {};
  tokens.forEach(t => counts[t] = (counts[t] || 0) + 1);
  
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, topK)
    .map(x => x[0]);
}

// --------------------------------------------------
// 4. Main Page Component
// --------------------------------------------------
export default function AdminContestRegister() {
  const [adminMode, setAdminMode] = useState(false);

  // 세션 데이터 모방 (Demo Master Data)
  const [companies, setCompanies] = useState(["씽굿", "KOSA", "OO대학교", "OO재단"]);
  const [managers, setManagers] = useState(["admin01", "manager02", "staff03"]);
  const [records, setRecords] = useState<any[]>([]);
  
  // 폼 상태
  const [status, setStatus] = useState(STATUS_OPTIONS[0]);
  const [hostOrgTypes, setHostOrgTypes] = useState<string[]>([]);
  const [companySearch, setCompanySearch] = useState("");
  const [hostCompany, setHostCompany] = useState("");
  const [newCompany, setNewCompany] = useState("");
  const [homepageUrl, setHomepageUrl] = useState("");
  const [keywords, setKeywords] = useState<string[]>([]);
  const [projectName, setProjectName] = useState("");
  const [applyStartDate, setApplyStartDate] = useState("");
  const [applyEndDate, setApplyEndDate] = useState("");
  const [extendedEndDate, setExtendedEndDate] = useState("");
  const [fields, setFields] = useState<string[]>([]);
  const [eligibilityRaw, setEligibilityRaw] = useState("");
  const [applyMethodType, setApplyMethodType] = useState(APPLY_METHOD_TYPES[0]);
  const [applyMethodUrl, setApplyMethodUrl] = useState("");
  const [region, setRegion] = useState("(선택)");
  const [prize1stAmount, setPrize1stAmount] = useState<number>(0);
  const [posterName, setPosterName] = useState<string | null>(null);
  
  const [managerSearch, setManagerSearch] = useState("");
  const [managerId, setManagerId] = useState("");
  const [newManager, setNewManager] = useState("");

  const [guideApplyPart, setGuideApplyPart] = useState("");
  const [guideTopic, setGuideTopic] = useState("");
  const [guidePrizeDetail, setGuidePrizeDetail] = useState("");
  const [guideSchedule, setGuideSchedule] = useState("");
  const [guideSubmitMethod, setGuideSubmitMethod] = useState("");
  const [guideJudgingCriteria, setGuideJudgingCriteria] = useState("");
  const [guideNotes, setGuideNotes] = useState("");

  const [lastResult, setLastResult] = useState<any>(null);

  // 필터링
  const filteredCompanies = useMemo(() => companies.filter(c => c.includes(companySearch.trim())), [companies, companySearch]);
  const filteredManagers = useMemo(() => managers.filter(m => m.includes(managerSearch.trim())), [managers, managerSearch]);

  const toggleArray = (arr: string[], setArr: (val: string[]) => void, item: string) => {
    if (arr.includes(item)) setArr(arr.filter(x => x !== item));
    else setArr([...arr, item]);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // 주최사/담당자 처리
    let hostCompanyFinal = hostCompany;
    if (newCompany.trim()) {
      if (!companies.includes(newCompany.trim())) setCompanies([...companies, newCompany.trim()]);
      hostCompanyFinal = newCompany.trim();
    } else if (hostCompany === "(검색 결과 없음)") {
      hostCompanyFinal = "";
    }

    let managerFinal = managerId;
    if (newManager.trim()) {
      if (!managers.includes(newManager.trim())) setManagers([...managers, newManager.trim()]);
      managerFinal = newManager.trim();
    } else if (managerId === "(검색 결과 없음)") {
      managerFinal = "";
    }

    // 자동 파싱
    const { ageMin, ageMax, conditionType, keywordHit } = parseEligibility(eligibilityRaw);
    
    // AI 키워드 추출
    const combinedText = [projectName, guideApplyPart, guideTopic, guidePrizeDetail, guideSchedule, guideSubmitMethod, guideJudgingCriteria, guideNotes].join(" ");
    const aiKeywords = extractKeywords(combinedText, 8);

    const payload = {
      status, host_org_types: hostOrgTypes, host_company: hostCompanyFinal, homepage_url: homepageUrl,
      keywords, project_name: projectName, apply_start_date: applyStartDate || null, apply_end_date: applyEndDate || null,
      extended_end_date: extendedEndDate || null, fields, eligibility_raw: eligibilityRaw,
      eligibility_age_min: ageMin, eligibility_age_max: ageMax, eligibility_condition_type: conditionType, eligibility_keyword: keywordHit,
      apply_method_type: applyMethodType, apply_method_url: applyMethodUrl, region: region === "(선택)" ? null : region,
      prize_1st_amount: prize1stAmount, poster_filename: posterName, manager_id: managerFinal,
      guide_apply_part: guideApplyPart, guide_topic: guideTopic, guide_prize_detail: guidePrizeDetail, guide_schedule: guideSchedule,
      guide_submit_method: guideSubmitMethod, guide_judging_criteria: guideJudgingCriteria, guide_notes: guideNotes,
      ai_keywords: aiKeywords, created_at: new Date().toLocaleString()
    };

    setRecords([...records, payload]);
    setLastResult({ eligibility: { ageMin, ageMax, conditionType, keywordHit }, aiKeywords });
  };

  const handleDownloadCSV = () => {
    if (records.length === 0) return;
    const header = Object.keys(records[0]).join(",") + "\n";
    const csv = header + records.map(r => Object.values(r).map(v => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" }); // UTF-8 BOM
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "demo_contests.csv";
    link.click();
  };

  // 스타일 설정 (Streamlit 느낌 모방)
  const styles = {
    container: { display: "flex", gap: "30px", maxWidth: "1400px", margin: "0 auto", padding: "20px", fontFamily: "sans-serif" },
    sidebar: { width: "250px", flexShrink: 0, padding: "20px", background: "#f8f9fa", borderRadius: "8px", border: "1px solid #ddd" },
    main: { flex: 2, display: "flex", flexDirection: "column" as const, gap: "20px" },
    rightPanel: { flex: 1, display: "flex", flexDirection: "column" as const, gap: "20px" },
    section: { background: "#fff", padding: "20px", borderRadius: "8px", border: "1px solid #ddd", marginBottom: "20px" },
    input: { width: "100%", padding: "8px", marginTop: "4px", marginBottom: "12px", border: "1px solid #ccc", borderRadius: "4px" },
    label: { fontWeight: "bold", fontSize: "0.9rem", color: "#333", marginTop: "10px", display: "block" },
    btn: { background: "#ff4b4b", color: "#fff", padding: "10px 16px", border: "none", borderRadius: "4px", cursor: "pointer", fontWeight: "bold" },
    btnOutline: { background: "#fff", color: "#333", padding: "8px 12px", border: "1px solid #ccc", borderRadius: "4px", cursor: "pointer", fontSize: "0.9rem" },
    checkboxGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))", gap: "8px", marginTop: "4px", marginBottom: "12px" }
  };

  if (!adminMode) {
    return (
      <div style={styles.container}>
        <aside style={styles.sidebar}>
          <h3>관리자 메뉴</h3>
          <label style={{ cursor: "pointer", fontWeight: "bold", display: "flex", alignItems: "center", gap: 8 }}>
            <input type="checkbox" checked={adminMode} onChange={(e) => setAdminMode(e.target.checked)} /> 관리자 모드 ON
          </label>
        </aside>
        <main style={{ flex: 1 }}>
          <div style={{ background: "#fff3cd", color: "#856404", padding: "16px", borderRadius: "4px", border: "1px solid #ffeeba" }}>
            관리자 모드가 OFF 상태입니다. 좌측 사이드바에서 <b>관리자 모드 ON</b>을 체크해 주세요.
          </div>
        </main>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <aside style={styles.sidebar}>
        <h3>관리자 메뉴</h3>
        {/* 홈으로 돌아가는 버튼 */}
        <Link href="/">
          <button style={{ ...styles.btnOutline, width: "100%", marginBottom: "10px" }}>
            ⬅️ 메인 홈으로 돌아가기
          </button>
        </Link>
        <label style={{ cursor: "pointer", ... }}>
          <input type="checkbox" ... /> 관리자 모드 ON
        </label>
      </aside>

      <div style={{ flex: 1, display: "flex", gap: "30px" }}>
        <main style={styles.main}>
          <h1 style={{ marginBottom: "10px" }}>관리자용 공모전 등록 (정형 데이터 중심 · 데모용)</h1>
          <form style={styles.section} onSubmit={handleSubmit}>
            <h3>기본 정보</h3>
            
            <label style={styles.label}>상태(status)</label>
            <div style={{ display: "flex", gap: 16 }}>
              {STATUS_OPTIONS.map(opt => (
                <label key={opt}><input type="radio" name="status" value={opt} checked={status === opt} onChange={(e) => setStatus(e.target.value)} /> {opt}</label>
              ))}
            </div>

            <label style={styles.label}>주최기관(정형 선택)</label>
            <div style={styles.checkboxGrid}>
              {HOST_ORG_TYPES.map(type => (
                <label key={type} style={{ fontSize: "0.85rem" }}><input type="checkbox" checked={hostOrgTypes.includes(type)} onChange={() => toggleArray(hostOrgTypes, setHostOrgTypes, type)} /> {type}</label>
              ))}
            </div>

            <hr style={{ margin: "20px 0", border: "0.5px solid #eee" }} />
            <h4>주최사(검색 선택 / 신규 추가)</h4>
            <input type="text" style={styles.input} placeholder="주최사 검색 (예: 씽굿)" value={companySearch} onChange={(e) => setCompanySearch(e.target.value)} />
            <select style={styles.input} value={hostCompany} onChange={(e) => setHostCompany(e.target.value)}>
              <option value="">(기존 목록에서 선택)</option>
              {filteredCompanies.length > 0 ? filteredCompanies.map(c => <option key={c} value={c}>{c}</option>) : <option disabled>(검색 결과 없음)</option>}
            </select>
            <input type="text" style={styles.input} placeholder="목록에 없으면 신규 주최사 입력(선택)" value={newCompany} onChange={(e) => setNewCompany(e.target.value)} />

            <label style={styles.label}>홈페이지 URL</label>
            <input type="text" style={styles.input} placeholder="https://..." value={homepageUrl} onChange={(e) => setHomepageUrl(e.target.value)} />

            <label style={styles.label}>키워드(정형 선택)</label>
            <div style={styles.checkboxGrid}>
              {KEYWORD_TAGS.map(tag => (
                <label key={tag} style={{ fontSize: "0.85rem" }}><input type="checkbox" checked={keywords.includes(tag)} onChange={() => toggleArray(keywords, setKeywords, tag)} /> {tag}</label>
              ))}
            </div>

            <label style={styles.label}>프로젝트명(text)</label>
            <input type="text" style={styles.input} placeholder="예: 2026 AI 아이디어 공모전" value={projectName} onChange={(e) => setProjectName(e.target.value)} required />

            <div style={{ display: "flex", gap: 10 }}>
              <div style={{ flex: 1 }}><label style={styles.label}>접수 시작일</label><input type="date" style={styles.input} value={applyStartDate} onChange={(e) => setApplyStartDate(e.target.value)} /></div>
              <div style={{ flex: 1 }}><label style={styles.label}>접수 마감일</label><input type="date" style={styles.input} value={applyEndDate} onChange={(e) => setApplyEndDate(e.target.value)} /></div>
              <div style={{ flex: 1 }}><label style={styles.label}>연장 마감일</label><input type="date" style={styles.input} value={extendedEndDate} onChange={(e) => setExtendedEndDate(e.target.value)} /></div>
            </div>

            <label style={styles.label}>공모 분야(정형 선택)</label>
            <div style={styles.checkboxGrid}>
              {CONTEST_FIELDS.map(f => (
                <label key={f} style={{ fontSize: "0.85rem" }}><input type="checkbox" checked={fields.includes(f)} onChange={() => toggleArray(fields, setFields, f)} /> {f}</label>
              ))}
            </div>

            <hr style={{ margin: "20px 0", border: "0.5px solid #eee" }} />
            <h4>참가 자격(자동 정형화)</h4>
            <input type="text" style={styles.input} placeholder="예: 만 19세 이상, 19세~39세, 청소년, 대학생 등" value={eligibilityRaw} onChange={(e) => setEligibilityRaw(e.target.value)} />

            <div style={{ display: "flex", gap: 10 }}>
              <div style={{ flex: 1 }}><label style={styles.label}>접수 방법(유형)</label><select style={styles.input} value={applyMethodType} onChange={(e) => setApplyMethodType(e.target.value)}>{APPLY_METHOD_TYPES.map(o => <option key={o}>{o}</option>)}</select></div>
              <div style={{ flex: 2 }}><label style={styles.label}>접수 방법 링크(URL)</label><input type="text" style={styles.input} placeholder="https://..." value={applyMethodUrl} onChange={(e) => setApplyMethodUrl(e.target.value)} /></div>
            </div>

            <div style={{ display: "flex", gap: 10 }}>
              <div style={{ flex: 1 }}><label style={styles.label}>참가 지역(정형)</label><select style={styles.input} value={region} onChange={(e) => setRegion(e.target.value)}><option>(선택)</option>{REGIONS.map(r => <option key={r}>{r}</option>)}</select></div>
              <div style={{ flex: 1 }}><label style={styles.label}>시상 규모(1등상금)</label><input type="number" style={styles.input} step="10000" min="0" value={prize1stAmount} onChange={(e) => setPrize1stAmount(Number(e.target.value))} /></div>
            </div>

            <label style={styles.label}>포스터 파일 업로드 (데모)</label>
            <input type="file" style={styles.input} accept="image/png, image/jpeg, image/webp" onChange={(e) => setPosterName(e.target.files?.[0]?.name || null)} />

            <hr style={{ margin: "20px 0", border: "0.5px solid #eee" }} />
            <h4>담당자(검색 선택 / 신규 추가)</h4>
            <input type="text" style={styles.input} placeholder="담당자 ID 검색" value={managerSearch} onChange={(e) => setManagerSearch(e.target.value)} />
            <select style={styles.input} value={managerId} onChange={(e) => setManagerId(e.target.value)}>
              <option value="">(기존 목록에서 선택)</option>
              {filteredManagers.length > 0 ? filteredManagers.map(m => <option key={m} value={m}>{m}</option>) : <option disabled>(검색 결과 없음)</option>}
            </select>
            <input type="text" style={styles.input} placeholder="신규 담당자 ID 입력" value={newManager} onChange={(e) => setNewManager(e.target.value)} />

            <hr style={{ margin: "20px 0", border: "1px solid #ccc" }} />
            <h3>공모요강 (컬럼은 고정, 내용은 텍스트)</h3>
            <label style={styles.label}>응모 부분</label><textarea style={{...styles.input, height: "60px"}} value={guideApplyPart} onChange={(e) => setGuideApplyPart(e.target.value)} />
            <label style={styles.label}>응모 주제</label><textarea style={{...styles.input, height: "60px"}} value={guideTopic} onChange={(e) => setGuideTopic(e.target.value)} />
            <label style={styles.label}>시상 내역</label><textarea style={{...styles.input, height: "60px"}} value={guidePrizeDetail} onChange={(e) => setGuidePrizeDetail(e.target.value)} />
            <label style={styles.label}>응모 일정</label><textarea style={{...styles.input, height: "60px"}} value={guideSchedule} onChange={(e) => setGuideSchedule(e.target.value)} />
            <label style={styles.label}>제출 방법</label><textarea style={{...styles.input, height: "60px"}} value={guideSubmitMethod} onChange={(e) => setGuideSubmitMethod(e.target.value)} />
            <label style={styles.label}>심사 기준</label><textarea style={{...styles.input, height: "60px"}} value={guideJudgingCriteria} onChange={(e) => setGuideJudgingCriteria(e.target.value)} />
            <label style={styles.label}>유의 사항</label><textarea style={{...styles.input, height: "80px"}} value={guideNotes} onChange={(e) => setGuideNotes(e.target.value)} />

            <button type="submit" style={{...styles.btn, width: "100%", marginTop: "20px"}}>등록 (데모)</button>
          </form>

          {lastResult && (
            <div style={{ background: "#d4edda", color: "#155724", padding: "15px", borderRadius: "8px", border: "1px solid #c3e6cb", marginBottom: "20px" }}>
              <h4>✅ 데모 등록 완료! (세션에만 저장됩니다)</h4>
              <pre style={{ background: "rgba(255,255,255,0.7)", padding: "10px", borderRadius: "4px", fontSize: "0.85rem", overflowX: "auto" }}>
                {JSON.stringify(lastResult, null, 2)}
              </pre>
            </div>
          )}
        </main>

        <aside style={styles.rightPanel}>
          <div style={styles.section}>
            <h3>등록된 데이터(세션)</h3>
            <div style={{ color: "#666", fontSize: "0.9rem", marginBottom: "16px" }}>현재 {records.length}건 등록됨</div>
            <button style={{...styles.btnOutline, width: "100%", marginBottom: "10px", background: "#e2e6ea"}} onClick={handleDownloadCSV} disabled={records.length === 0}>
              📥 등록 데이터 CSV 다운로드 (데모)
            </button>
            <button style={{...styles.btnOutline, width: "100%", color: "#d9534f", borderColor: "#d9534f"}} onClick={() => { setRecords([]); setLastResult(null); }}>
              🗑️ 세션 데이터 초기화
            </button>
          </div>

          <div style={styles.section}>
            <h3>마스터 목록(데모)</h3>
            <div style={{ fontSize: "0.9rem", marginBottom: "10px" }}>
              <strong>주최사 목록 (세션):</strong>
              <div style={{ background: "#f8f9fa", padding: "8px", borderRadius: "4px", marginTop: "4px" }}>{companies.join(", ")}</div>
            </div>
            <div style={{ fontSize: "0.9rem" }}>
              <strong>담당자 목록 (세션):</strong>
              <div style={{ background: "#f8f9fa", padding: "8px", borderRadius: "4px", marginTop: "4px" }}>{managers.join(", ")}</div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
