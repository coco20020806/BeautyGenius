import { BookOpen, Sparkles, UserRound } from 'lucide-react';
import { BottomNav } from '../components/BottomNav';
import { MobileShell } from '../components/MobileShell';

interface PlaceholderPageProps {
  title: string;
}

export function PlaceholderPage({ title }: PlaceholderPageProps) {
  const Icon = title === '知识库' ? BookOpen : title === '我的' ? UserRound : Sparkles;
  return (
    <MobileShell withNav className="placeholder-page">
      <header className="page-heading"><span className="page-kicker">COMING NEXT</span><h1>{title}</h1></header>
      <section className="placeholder-card">
        <span><Icon size={30} /></span>
        <h2>{title}功能正在准备中</h2>
        <p>本期先完成教程上传、照片确认、视频解析与妆容适配流程。</p>
      </section>
      <BottomNav />
    </MobileShell>
  );
}
