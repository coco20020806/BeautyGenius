import { ArrowLeft, Camera, Check, ImagePlus, LockKeyhole, ShieldCheck, SunMedium, UserRound } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MobileShell } from '../components/MobileShell';
import { makeupService } from '../services/makeupService';

export function PhotoPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const previousUrl = useRef('');

  useEffect(() => () => {
    if (previousUrl.current) URL.revokeObjectURL(previousUrl.current);
  }, []);

  function choosePhoto(nextFile: File | null) {
    if (previousUrl.current) URL.revokeObjectURL(previousUrl.current);
    const nextUrl = nextFile ? URL.createObjectURL(nextFile) : '';
    previousUrl.current = nextUrl;
    setFile(nextFile);
    setPreviewUrl(nextUrl);
    setError('');
  }

  async function continueFlow(skipped: boolean) {
    if (loading) return;
    if (!skipped && !file) return;
    setLoading(true);
    setError('');
    try {
      const result = await makeupService.uploadPhoto(skipped ? null : file);
      sessionStorage.setItem(
        'makeupPhoto',
        JSON.stringify({ skipped: result.skipped, fileName: file?.name ?? null }),
      );
      navigate('/parsing');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '照片上传失败，请重试');
    } finally {
      setLoading(false);
    }
  }

  return (
    <MobileShell className="photo-page">
      <header className="detail-header">
        <button className="icon-button" type="button" aria-label="返回" onClick={() => navigate(-1)}><ArrowLeft size={21} /></button>
        <div><span className="page-kicker">STEP 02</span><h1>确认照片</h1></div>
        <span className="header-spacer" />
      </header>

      <section className="photo-preview" aria-label="照片预览区域">
        {previewUrl ? (
          <img src={previewUrl} alt="待确认的本人照片" />
        ) : (
          <div className="portrait-placeholder" aria-hidden="true">
            <span className="portrait-placeholder__halo" />
            <UserRound size={82} strokeWidth={1.15} />
          </div>
        )}
        <span className="photo-preview__badge"><Camera size={15} />{file ? '照片已就绪' : '正面照片'}</span>
      </section>

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

      {error ? <p className="upload-error" role="alert">{error}</p> : null}

      <div className="photo-actions">
        <input
          id="photo-upload"
          className="visually-hidden"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          aria-label="上传本人照片"
          onChange={(event) => choosePhoto(event.target.files?.[0] ?? null)}
        />
        <label className="secondary-button" htmlFor="photo-upload">{file ? '重新上传' : '选择照片'}</label>
        <button className="primary-button" type="button" disabled={!file || loading} onClick={() => void continueFlow(false)}>
          {loading ? '上传中…' : '确认上传'}
        </button>
      </div>
      <button className="text-button" type="button" disabled={loading} onClick={() => void continueFlow(true)}>暂时跳过</button>
      <p className="skip-explainer">跳过后将使用默认示意脸生成教程图示</p>
    </MobileShell>
  );
}
