import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "씽굿 큐레이션",
  description: "ThinkGood AI 추천 시스템 서비스입니다.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
