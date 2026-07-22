import { ArrowLeft, Camera, Check, ImagePlus, LockKeyhole, ShieldCheck, SunMedium, UserRound, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MobileShell } from '../components/MobileShell';
import femaleAverageFace from '../assets/female-average-face.png';
import { HttpError } from '../services/httpClient';
import { makeupService } from '../services/makeupService';

export function PhotoPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [loadingAction, setLoadingAction] = useState<'skip' | 'upload' | null>(null);
  const [error, setError] = useState('');
  const [exampleOpen, setExampleOpen] = useState(false);
  const previousUrl = useRef('');

  useEffect(() => () => {
    if (previousUrl.current) URL.revokeObjectURL(previousUrl.current);
  }, []);

  useEffect(() => {
    if (!exampleOpen) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setExampleOpen(false);
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [exampleOpen]);

  function choosePhoto(nextFile: File | null) {
    if (previousUrl.current) URL.revokeObjectURL(previousUrl.current);
    const nextUrl = nextFile ? URL.createObjectURL(nextFile) : '';
    previousUrl.current = nextUrl;
    setFile(nextFile);
    setPreviewUrl(nextUrl);
    setError('');
  }

  async function continueFlow(skipped: boolean) {
    if (loadingAction) return;
    if (!skipped && !file) return;
    setLoadingAction(skipped ? 'skip' : 'upload');
    setError('');
    try {
      const result = await makeupService.uploadPhoto(skipped ? null : file);
      sessionStorage.setItem(
        'makeupPhoto',
        JSON.stringify({ skipped: result.skipped, fileName: file?.name ?? null }),
      );
      navigate('/parsing');
    } catch (reason) {
      if (reason instanceof HttpError && reason.code === 'USER_PHOTO_REJECTED') {
        setError(reason.message || '照片未通过审核，请按拍摄指引重新上传');
      } else {
        setError(reason instanceof Error ? reason.message : '照片上传失败，请重试');
      }
    } finally {
      setLoadingAction(null);
    }
  }

  const loading = loadingAction !== null;

  return (
    <MobileShell className="photo-page">
      <header className="detail-header">
        <button className="icon-button" type="button" aria-label="返回" onClick={() => navigate(-1)}><ArrowLeft size={21} /></button>
        <div><span className="page-kicker">STEP 02</span><h1>确认照片</h1></div>
        <span className="header-spacer" />
      </header>

      <input
        id="photo-upload"
        className="visually-hidden"
        type="file"
        accept="image/jpeg,image/png,image/webp"
        aria-label="上传本人照片"
        onChange={(event) => choosePhoto(event.target.files?.[0] ?? null)}
      />

      <label className="photo-preview photo-preview--upload" htmlFor="photo-upload" aria-label="照片预览区域">
        {previewUrl ? (
          <img src={previewUrl} alt="待确认的本人照片" />
        ) : (
          <div className="portrait-placeholder" aria-hidden="true">
            <span className="portrait-placeholder__halo" />
            <UserRound size={82} strokeWidth={1.15} />
          </div>
        )}
        <span className="photo-preview__badge"><Camera size={15} />{file ? '照片已就绪' : '上传正面照片'}</span>
      </label>

      <button
        className="portrait-example-trigger"
        type="button"
        onClick={() => setExampleOpen(true)}
      >
        查看标准人像照片示例
      </button>

      {error ? <p className="upload-error" role="alert">{error}</p> : null}

      <div className="photo-skip">
        <button className="primary-button photo-skip__button" type="button" disabled={loading} onClick={() => void continueFlow(true)}>
          {loadingAction === 'skip' ? '处理中…' : '暂时跳过（使用标准人脸生成）'}
        </button>
        <p className="skip-explainer">推荐先跳过，使用默认示意脸即可继续生成教程图示</p>
      </div>

      <div className="photo-actions">
        <p className="photo-actions__hint">也可以点击上方人像上传本人照片，效果会更贴近你</p>
        <div className="photo-actions__row photo-actions__row--single">
          <button className="photo-confirm-button" type="button" disabled={!file || loading} onClick={() => void continueFlow(false)}>
            {loadingAction === 'upload' ? '正在审核照片…' : '确认上传'}
          </button>
        </div>
      </div>

      <section className="photo-value-card">
        <div className="section-title-row">
          <span className="section-icon"><ImagePlus size={18} /></span>
          <div><span className="section-eyebrow">更贴近你的效果</span><h2>上传照片的价值</h2></div>
        </div>
        <p>我们会用照片生成更贴近你的妆后预览，并调整上妆范围与位置。</p>
        <ul className="photo-tips">
          <li><span><UserRound size={16} /></span><div><strong>正面清晰</strong><small>保持自然表情，完整露出五官</small></div><Check size={16} /></li>
          <li><span><SunMedium size={16} /></span><div><strong>光线自然</strong><small>避免强逆光或彩色灯光</small></div><Check size={16} /></li>
          <li><span><ShieldCheck size={16} /></span><div><strong>尽量无遮挡</strong><small>不戴口罩或大面积遮挡面部</small></div><Check size={16} /></li>
        </ul>
      </section>

      <div className="privacy-note"><LockKeyhole size={15} /><p>照片仅用于生成个人化预览和适配建议，你可以随时删除。</p></div>

      {exampleOpen ? (
        <div
          className="step-clip-overlay"
          role="dialog"
          aria-modal="true"
          aria-label="标准人像照片示例"
          onClick={(event) => {
            if (event.target === event.currentTarget) setExampleOpen(false);
          }}
        >
          <div className="step-clip-panel portrait-example-panel">
            <header className="step-clip-panel__header">
              <h2>标准人像照片示例</h2>
              <button className="icon-button" type="button" aria-label="关闭示例" onClick={() => setExampleOpen(false)}>
                <X size={20} />
              </button>
            </header>
            <img
              className="portrait-example-panel__image"
              src={femaleAverageFace}
              alt="标准人像平均脸示例"
            />
            <p className="portrait-example-panel__caption">跳过上传时将使用此平均脸底图生成预览</p>
          </div>
        </div>
      ) : null}
    </MobileShell>
  );
}
