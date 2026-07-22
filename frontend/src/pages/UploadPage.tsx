import { Check, ChevronRight, CloudUpload, Film, RefreshCw, Sparkles, Zap, EyeOff } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BottomNav } from '../components/BottomNav';
import { MobileShell } from '../components/MobileShell';
import { makeupService } from '../services/makeupService';
import recentDate from '../assets/recent-date.png';
import recentNaturalDaily from '../assets/recent-natural-daily.png';
import recentSheer from '../assets/recent-sheer.png';

const recentTasks = [
  { name: '自然日常妆', date: '2026-07-20', status: '适配完成', cover: recentNaturalDaily },
  { name: '清透妆容', date: '2026-07-18', status: '可继续', cover: recentSheer },
  { name: '约会妆容', date: '2026-07-15', status: '解析完成', cover: recentDate },
];

function formatSize(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function UploadPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [fastParse, setFastParse] = useState(true);
  const [skipMakeupPreview, setSkipMakeupPreview] = useState(false);
  const [devSkipLoading, setDevSkipLoading] = useState(false);
  const [devSkipError, setDevSkipError] = useState('');

  const showDevSkip =
    import.meta.env.DEV || import.meta.env.VITE_SHOW_DEV_SKIP === '1';

  async function skipToPreviewDev() {
    if (devSkipLoading) return;
    setDevSkipLoading(true);
    setDevSkipError('');
    try {
      const result = await makeupService.skipToDevPreview();
      sessionStorage.setItem(
        'makeupTask',
        JSON.stringify({ taskId: result.taskId, devSkip: true }),
      );
      sessionStorage.removeItem('makeupProgress');
      navigate('/preview');
    } catch (reason) {
      const message =
        reason instanceof Error ? reason.message : '无法加载本地预览';
      if (/not found/i.test(message)) {
        setDevSkipError(
          'API 返回 Not Found：8000 端口可能是旧版服务。请关闭所有 API 后重新运行 .\\scripts\\run-dev.ps1 或 .\\scripts\\run-api.ps1',
        );
      } else {
        setDevSkipError(message);
      }
    } finally {
      setDevSkipLoading(false);
    }
  }

  async function continueFlow() {
    if (!file || loading) return;
    setLoading(true);
    setError('');
    try {
      const result = await makeupService.uploadVideo(file, { fastParse, skipMakeupPreview });
      sessionStorage.setItem('makeupTask', JSON.stringify(result));
      navigate('/photo');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '视频上传失败，请重新选择');
    } finally {
      setLoading(false);
    }
  }

  return (
    <MobileShell withNav className="upload-page">
      <header className="page-heading">
        <span className="page-kicker">MAKEUP PRACTICE</span>
        <h1>上传教程</h1>
      </header>

      <section className={`upload-card${file ? ' has-file' : ''}`} aria-labelledby="upload-title">
        <input
          id="video-upload"
          className="visually-hidden"
          type="file"
          accept="video/mp4,video/quicktime,.mp4,.mov"
          aria-label="选择教程视频"
          onChange={(event) => {
            setFile(event.target.files?.[0] ?? null);
            setError('');
          }}
        />
        <label htmlFor="video-upload" className="upload-card__label">
          <span className="upload-card__icon">{file ? <Film size={29} /> : <CloudUpload size={31} />}</span>
          <span id="upload-title" className="upload-card__title">{file ? file.name : '上传你的教程视频'}</span>
          <span className="upload-card__meta">{file ? `${formatSize(file.size)} · 点击重新选择` : '支持 MP4、MOV · 不超过 500MB'}</span>
        </label>
        {file && <Check className="upload-card__check" aria-hidden="true" size={19} />}
      </section>
      <p className="upload-card__hint">建议视频不应过长、过大，否则无法正常解析，建议&lt;5min、大小&lt;50MB</p>
      {error && <p className="inline-error" role="alert">{error}</p>}

      <label className="option-row" htmlFor="fast-parse">
        <input
          id="fast-parse"
          type="checkbox"
          checked={fastParse}
          onChange={(event) => setFastParse(event.target.checked)}
        />
        <span className="option-row__icon" aria-hidden="true"><Zap size={17} /></span>
        <span className="option-row__body">
          <strong>快速解析</strong>
          <small>少做一些精细检查，更快出教程</small>
        </span>
      </label>

      <label className="option-row" htmlFor="skip-makeup-preview">
        <input
          id="skip-makeup-preview"
          type="checkbox"
          checked={skipMakeupPreview}
          onChange={(event) => setSkipMakeupPreview(event.target.checked)}
          aria-label="跳过妆容预览"
        />
        <span className="option-row__icon" aria-hidden="true"><EyeOff size={17} /></span>
        <span className="option-row__body">
          <strong>跳过妆容预览</strong>
          <small>不生成试妆效果图，直接进下一步</small>
        </span>
      </label>

      <section className="requirement-card" aria-labelledby="requirements-title">
        <div className="section-title-row">
          <span className="section-icon"><Sparkles size={18} /></span>
          <div><span className="section-eyebrow">上传前看一眼</span><h2 id="requirements-title">视频要求</h2></div>
        </div>
        <ul className="requirement-list">
          <li><Check size={15} />教程步骤明显</li>
          <li><Check size={15} />人脸清晰无遮挡</li>
          <li><Check size={15} />光线充足稳定</li>
        </ul>
      </section>

      {file && (
        <button className="primary-button" type="button" onClick={continueFlow} disabled={loading}>
          {loading ? <><RefreshCw className="spin" size={18} />正在准备</> : <>下一步<ChevronRight size={18} /></>}
        </button>
      )}

      <section className="recent-section" aria-labelledby="recent-title">
        <div className="section-heading"><h2 id="recent-title">最近任务</h2><button type="button">查看全部</button></div>
        <div className="task-list">
          {recentTasks.map((task) => (
            <button className="task-card" type="button" key={task.name}>
              <span className="task-card__thumb">
                <img src={task.cover} alt="" />
              </span>
              <span className="task-card__body"><strong>{task.name}</strong><small>{task.date} · {task.status}</small></span>
              <ChevronRight size={17} aria-hidden="true" />
            </button>
          ))}
        </div>
      </section>

      {showDevSkip ? (
        <div className="dev-skip-wrap">
          <button
            className="dev-skip-button"
            type="button"
            disabled={devSkipLoading}
            onClick={() => void skipToPreviewDev()}
          >
            {devSkipLoading ? '正在加载本地预览…' : '跳过前两步（开发）'}
          </button>
          {devSkipError ? (
            <p className="inline-error" role="alert">
              {devSkipError}
            </p>
          ) : (
            <p className="dev-skip-hint">使用 configs/dev-pinned-runs.json 中的固定 parse / preview run</p>
          )}
        </div>
      ) : null}

      <BottomNav />
    </MobileShell>
  );
}
