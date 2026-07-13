"use client";

import { useState } from "react";

export default function Home() {
  const [userId, setUserId] = useState("");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);

  const handleLogin = async () => {
    if (!userId.startsWith("M")) {
      alert("잘못된 아이디 형식입니다. 'M'으로 시작하는 아이디를 입력해주세요.");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`/api/recommend/${userId}`);
      const json = await res.json();
      setData(json);
      setIsLoggedIn(true);
    } catch (error) {
      alert("데이터를 불러오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUserId("");
    setData(null);
  };

  if (!isLoggedIn) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="bg-white p-12 rounded-xl shadow-sm border border-gray-200 text-center w-full max-w-md">
          <h1 className="text-3xl font-extrabold text-gray-900 mb-2">누구나 도전을 꿈꾸고 경험하도록</h1>
          <p className="text-gray-500 mb-8 font-medium">오늘 더 나은 세상을 만들어 갑니다.</p>
          <input
            type="text"
            placeholder="M24_..."
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            className="w-full border border-gray-300 p-3 rounded-md mb-4 focus:outline-none focus:border-red-500"
          />
          <button
            onClick={handleLogin}
            disabled={loading}
            className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-4 rounded-md transition-colors"
          >
            {loading ? "로딩중..." : "시작하기"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8 pb-4 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-800">안녕하세요, {userId}님!</h2>
          <button
            onClick={handleLogout}
            className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-md"
          >
            Logout
          </button>
        </div>

        <h3 className="text-xl font-bold text-gray-800 mb-4">오늘의 맞춤 추천 ({data?.segment})</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {data?.recommendations?.slice(0, 4).map((item: any, idx: number) => (
            <div key={idx} className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow flex flex-col h-[350px]">
              <div className="h-[150px] bg-gray-100 flex items-center justify-center shrink-0 border-b border-gray-100">
                {item.img_url ? (
                  <img src={item.img_url} alt="poster" className="w-full h-full object-cover" />
                ) : (
                  <span className="text-gray-400 font-medium">NO IMAGE</span>
                )}
              </div>
              <div className="p-4 flex flex-col grow">
                <div className="mb-2">
                  <span className="bg-red-600 text-white text-xs font-bold py-1 px-2 rounded mr-1">추천</span>
                  <span className="bg-gray-100 text-gray-600 text-xs py-1 px-2 rounded">{item.분야_한글?.split(",")[0] || "기타"}</span>
                </div>
                <div className="text-gray-900 font-bold leading-tight line-clamp-2">{item.program_nm}</div>
                <div className="mt-auto text-red-600 text-sm font-bold truncate">{item.reason_tag || "추천"}</div>
              </div>
              <div className="bg-gray-800 text-white px-4 py-2 flex justify-between items-center shrink-0">
                <span className="text-xs text-gray-400 font-bold">종합 적합도</span>
                <span className="text-red-400 font-black text-sm">{item.final_score}점</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
