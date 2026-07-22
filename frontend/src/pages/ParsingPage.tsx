import { Check, Circle, LoaderCircle, RefreshCw, Sparkles } from 'lucide-react';
import type { CSSProperties } from 'react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MobileShell } from '../components/MobileShell';
import { fetchAnalysisSnapshot, isServerBusyError, makeupService } from '../services/makeupService';
import type { AnalysisProgress, AnalysisStage } from '../types/makeup';

const initialStages: AnalysisStage[] = [
  { id: 'quality-check', label: '检查视频质量', status: 'active' },
  { id: 'step-detection', label: '识别妆容步骤', status: 'pending' },
  { id: 'preview-generation', label: '生成适配预览', status: 'pending' },
  { id: 'hint-generation', label: '整理关键建议', status: 'pending' },
];

const QUEUE_POLL_MS = 5000;

function readTaskId() {
  try {
    return JSON.parse(sessionStorage.getItem('makeupTask') ?? '{}').taskId ?? 'demo-task';
  } catch {
    return 'demo-task';
  }
}

function readCachedProgress(taskId: string): AnalysisProgress | null {
  try {
    const raw = sessionStorage.getItem('makeupProgress');
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AnalysisProgress;
    return parsed.taskId === taskId ? parsed : null;
  } catch {
    return null;
  }
}

export function ParsingPage() {
  const navigate = useNavigate();
  const taskId = readTaskId();
  const [runId, setRunId] = useState(0);
  const [progress, setProgress] = useState<AnalysisProgress>(() => {
    const cached = readCachedProgress(taskId);
    return cached ?? {
      taskId,
      progress: 8,
      currentStage: '检查视频质量',
      remainingSeconds: 30,
      status: 'processing',
      stages: initialStages,
    };
  });

  const retry = useCallback(() => {
    setProgress((current) => ({
      ...current,
      progress: 8,
      status: 'processing',
      failureReason: undefined,
      detailMessage: undefined,
      stages: initialStages,
    }));
    setRunId((value) => value + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      const snapshot = await fetchAnalysisSnapshot(taskId);
      if (snapshot && !cancelled) {
        setProgress(snapshot);
        if (snapshot.status === 'completed') {
          navigate('/preview');
          return;
        }
        if (snapshot.status === 'failed') {
          return;
        }
      }
      try {
        for await (const next of makeupService.analyze(taskId)) {
          if (cancelled) return;
          setProgress(next);
          sessionStorage.setItem('makeupProgress', JSON.stringify(next));
          if (next.status === 'completed') {
            navigate('/preview');
            return;
          }
        }
      } catch (reason) {
        if (!cancelled) {
          if (isServerBusyError(reason)) {
            setProgress((current) => ({
              ...current,
              status: 'queued',
              currentStage: '排队中',
              failureReason: reason instanceof Error ? reason.message : '排队中，请稍后再试',
            }));
            return;
          }
          setProgress((current) => ({
            ...current,
            status: 'failed',
            failureReason: reason instanceof Error ? reason.message : '解析暂时中断，请重新尝试',
          }));
        }
      }
    }
    void run();
    return () => { cancelled = true; };
  }, [navigate, runId, taskId]);

  useEffect(() => {
    if (progress.status !== 'queued') return;
    let cancelled = false;
    const timer = window.setInterval(() => {
      void (async () => {
        try {
          const status = await makeupService.getServerStatus();
          if (!cancelled && !status.busy) retry();
        } catch {
          /* keep waiting */
        }
      })();
    }, QUEUE_POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [progress.status, retry]);

  const stageTitle =
    progress.currentStage === '检查视频质量' &&
    typeof progress.detailMessage === 'string' &&
    progress.detailMessage.includes('压缩')
      ? '压缩视频以便分析'
      : progress.currentStage;

  const isQueued = progress.status === 'queued';
  const isFailed = progress.status === 'failed';

  return (
    <MobileShell className="parsing-page">
      <header className="centered-heading">
        <span className="page-kicker">AI MAKEUP ANALYSIS</span>
        <h1>{isQueued ? '排队中' : isFailed ? '解析遇到问题' : '解析中，请稍候…'}</h1>
        <p>
          {isQueued
            ? '服务器已满（最多 2 人同时使用），有空位后将自动重试'
            : isFailed
              ? '你的视频和照片都已保留'
              : '正在把教程变成适合你的上妆方案'}
        </p>
      </header>

      <section className="progress-hero" aria-label={`解析进度 ${progress.progress}%`}>
        <div className="progress-ring" style={{ '--progress': isQueued ? 0 : progress.progress } as CSSProperties}>
          <div className="progress-ring__inner">
            <strong>{isQueued ? <LoaderCircle className="spin" size={28} /> : <>{progress.progress}<small>%</small></>}</strong>
            <span>{isQueued ? '排队中' : progress.status === 'completed' ? '已完成' : '解析进度'}</span>
          </div>
        </div>
        <div className="current-stage">
          <Sparkles size={16} /><span>当前阶段</span><strong>{isQueued ? '排队中' : stageTitle}</strong>
        </div>
        {progress.detailMessage && !isQueued ? (
          <p className="current-stage-detail">{progress.detailMessage}</p>
        ) : null}
      </section>

      <section className="stage-card" aria-labelledby="stage-title">
        <div className="section-heading"><h2 id="stage-title">处理步骤</h2><span>{progress.stages.filter((stage) => stage.status === 'completed').length}/{progress.stages.length}</span></div>
        <ol className="stage-list">
          {progress.stages.map((stage) => (
            <li key={stage.id} className={`stage-list__item is-${stage.status}`}>
              <span className="stage-list__icon">
                {stage.status === 'completed' ? <Check size={15} /> : stage.status === 'active' ? <LoaderCircle className="spin" size={16} /> : <Circle size={13} />}
              </span>
              <span>{stage.label}</span>
              <small>{stage.status === 'completed' ? '已完成' : stage.status === 'active' ? '处理中' : '等待中'}</small>
            </li>
          ))}
        </ol>
      </section>

      {isQueued ? (
        <div className="analysis-error" role="status">
          <p>{progress.failureReason ?? '排队中，请稍后再试'}</p>
          <button className="primary-button" type="button" onClick={retry}><RefreshCw size={17} />再试一次</button>
        </div>
      ) : null}

      {isFailed ? (
        <div className="analysis-error" role="alert"><p>{progress.failureReason}</p><button className="primary-button" type="button" onClick={retry}><RefreshCw size={17} />重新解析</button></div>
      ) : null}
    </MobileShell>
  );
}
