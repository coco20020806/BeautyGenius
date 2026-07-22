import { Bell, ChevronRight, Palette, ShieldCheck, Sparkles, UserRound } from 'lucide-react';
import { useState } from 'react';
import { BottomNav } from '../components/BottomNav';
import { MobileShell } from '../components/MobileShell';

function readProfile() {
  try { return { style: '清透自然', reminders: true, ...JSON.parse(localStorage.getItem('makeupProfile') ?? '{}') }; }
  catch { return { style: '清透自然', reminders: true }; }
}

export function ProfilePage() {
  const [profile, setProfile] = useState(readProfile);

  function save(next: typeof profile) {
    setProfile(next);
    localStorage.setItem('makeupProfile', JSON.stringify(next));
  }

  return (
    <MobileShell withNav className="learning-page profile-page">
      <header className="profile-heading"><span className="page-kicker">MY BEAUTY PROFILE</span></header>
      <section className="profile-hero"><span className="profile-avatar"><UserRound size={29} /></span><div><h2>美妆学习者</h2><p>清透妆容·新手进阶中</p></div><button type="button" aria-label="编辑个人资料"><ChevronRight size={18} /></button></section>
      <section className="profile-stats" aria-label="学习数据"><div><strong>12</strong><span>收藏教程</span></div><div><strong>28</strong><span>完成步骤</span></div><div><strong>6</strong><span>定制方案</span></div></section>
      <section className="profile-panel"><div className="section-heading"><h2>妆容档案</h2><span><Sparkles size={13} />已同步</span></div><div className="profile-tags"><span>混合肌</span><span>暖中性肤色</span><span>内双眼型</span></div></section>
      <section className="profile-panel profile-settings" aria-label="个人设置">
        <div className="profile-setting-static"><span><Palette size={17} /></span><div><strong>偏好风格</strong><small>{profile.style}</small></div></div>
        <button type="button" onClick={() => save({ ...profile, reminders: !profile.reminders })}><span><Bell size={17} /></span><div><strong>学习提醒</strong><small>{profile.reminders ? '已开启' : '已关闭'}</small></div><i className={profile.reminders ? 'is-on' : ''} aria-hidden="true" /></button>
        <button type="button"><span><ShieldCheck size={17} /></span><div><strong>隐私与数据</strong><small>管理照片和解析结果</small></div><ChevronRight size={16} /></button>
      </section>
      <BottomNav />
    </MobileShell>
  );
}
