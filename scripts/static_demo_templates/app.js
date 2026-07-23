/* Beauty Genius static demo — full flow + pager (incl. step diagrams when exported) */
(function () {
  'use strict';

  const DATA = window.DEMO_DATA;
  if (!DATA || !DATA.preview || !DATA.tutorial) {
    document.getElementById('shell').innerHTML =
      '<p style="padding:24px;color:#9e4149">缺少 assets/data.js，请先运行 python scripts/export_static_demo.py</p>';
    return;
  }

  const PAGES = [
    { id: 'upload', label: '上传' },
    { id: 'photo', label: '选图' },
    { id: 'parsing', label: '解析' },
    { id: 'preview', label: '预览' },
    { id: 'practice', label: '跟练' },
  ];
  if (DATA.stepDiagrams && Array.isArray(DATA.stepDiagrams.steps) && DATA.stepDiagrams.steps.length) {
    PAGES.push({ id: 'examples', label: '示例图' });
  }
  PAGES.push({ id: 'adjust', label: '微调' });

  const PART_LABELS = {
    prep: '妆前',
    base: '底妆',
    concealer: '遮瑕',
    set: '定妆',
    brow: '眉毛',
    eye: '眼睛',
    contour: '修容',
    highlight: '高光',
    cheek: '腮红',
    lip: '唇妆',
    other: '其他',
  };

  const STYLE_OPTIONS = ['清透自然', '甜美元气', '清冷高级', '性感成熟', '个性酷感'];
  const OCCASION_OPTIONS = ['日常上学', '通勤工作', '约会聚会', '艺术妆造'];
  const RETAINED_PART_OPTIONS = ['修容', '腮红', '眼妆'];
  const SKIN_TYPE_OPTIONS = ['油性肌肤', '干性肌肤', '混合性肌肤', '敏感肌'];
  const CONCERN_OPTIONS = [
    '增加立体感',
    '减少脸部留白',
    '弱化轮廓感',
    '放大眼睛',
    '降低眼位',
    '缩短中庭',
  ];
  const CONSTRAINT_OPTIONS = [
    '没有专业刷具',
    '产品不齐全',
    '早上时间少',
    '不会复杂眼妆',
    '不喜欢厚重底妆',
  ];

  const state = {
    route: 'upload',
    intensityId: 'L4',
    sliderPos: 50,
    collectMode: false,
    selectedStepIds: [],
    adjust: {
      style: '',
      occasions: [],
      retainedParts: [],
      skinType: '混合性肌肤',
      concerns: [],
      constraints: [],
    },
    clip: null,
  };

  const shell = document.getElementById('shell');
  const overlay = document.getElementById('clip-overlay');
  const toastEl = document.getElementById('toast');
  const pagerPrev = document.getElementById('pager-prev');
  const pagerNext = document.getElementById('pager-next');
  const pagerMeta = document.getElementById('pager-meta');
  let toastTimer = null;
  let clipCleanup = null;

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function showToast(message) {
    toastEl.textContent = message;
    toastEl.hidden = false;
    if (toastTimer) window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => {
      toastEl.hidden = true;
    }, 2200);
  }

  function pageIndex(route) {
    if (route === 'collected') {
      const examplesIdx = PAGES.findIndex((p) => p.id === 'examples');
      return examplesIdx >= 0 ? examplesIdx : -1;
    }
    return PAGES.findIndex((p) => p.id === route);
  }

  function formatSize(bytes) {
    const n = Number(bytes) || 0;
    if (n < 1024 * 1024) return `${Math.max(1, Math.round(n / 1024))} KB`;
    return `${(n / 1024 / 1024).toFixed(1)} MB`;
  }

  function navigate(route) {
    const allowed = PAGES.some((p) => p.id === route) || route === 'collected';
    if (!allowed) return;
    state.route = route;
    if (route === 'collected') {
      state.collectMode = false;
    } else if (route === 'examples') {
      state.collectMode = false;
    } else {
      state.collectMode = false;
      state.selectedStepIds = [];
    }
    closeClip();
    if (window.location.hash.replace(/^#/, '') !== route) {
      window.location.hash = route;
    }
    render();
  }

  function goRelative(delta) {
    const idx = pageIndex(state.route);
    const next = idx + delta;
    if (next < 0 || next >= PAGES.length) return;
    navigate(PAGES[next].id);
  }

  function updatePager() {
    const idx = pageIndex(state.route);
    const page = PAGES[idx] || PAGES[0];
    if (pagerPrev) {
      pagerPrev.disabled = idx <= 0;
      pagerPrev.classList.toggle('is-disabled', idx <= 0);
    }
    if (pagerNext) {
      pagerNext.disabled = idx >= PAGES.length - 1;
      pagerNext.classList.toggle('is-disabled', idx >= PAGES.length - 1);
    }
    if (pagerMeta) {
      pagerMeta.textContent = `${idx + 1} / ${PAGES.length} · ${page.label}`;
    }
  }

  function readHash() {
    const hash = (window.location.hash || '#upload').replace(/^#/, '');
    if (hash === 'collected') return 'collected';
    if (PAGES.some((p) => p.id === hash)) return hash;
    return 'upload';
  }

  function formatProductLine(step) {
    const display = (step.display_product || '').trim();
    if (display) return display;
    const name = (step.product && step.product.name ? step.product.name : '').trim();
    if (name && name !== 'unknown') return name;
    const kw = step.product && step.product.keywords && step.product.keywords[0];
    if (typeof kw === 'string' && kw.trim() && kw.trim().length > 2) return kw.trim();
    const primary = (step.taxonomy_primary || '').trim();
    if (primary) return primary;
    if (step.part && PART_LABELS[step.part]) return PART_LABELS[step.part];
    if (typeof kw === 'string' && kw.trim()) return kw.trim();
    return '无';
  }

  function formatRangeText(step) {
    const display = (step.display_range || '').trim();
    if (display) return display;
    const position =
      step.visual_layer && step.visual_layer.position
        ? String(step.visual_layer.position).trim()
        : '';
    return position || '无';
  }

  function formatTechnique(step) {
    const technique = (step.technique || '').trim();
    if (technique) return technique;
    const instruction = (step.instruction || '').trim();
    return instruction || '无';
  }

  function groupHeading(group) {
    const title = (group.title || '').trim() || '步骤';
    return `步骤 ${group.index} · ${title}`;
  }

  function stepSegmentTitle(step) {
    const display = (step.display_title || '').trim();
    if (display) return display;
    return (step.taxonomy_primary || '').trim() || step.step_id;
  }

  function resolveTutorialGroups(tutorial) {
    const byId = new Map((tutorial.steps || []).map((s) => [s.step_id, s]));
    const groups = tutorial.step_groups;
    if (groups && groups.length) {
      return groups.map((group) => ({
        group,
        steps: (group.step_ids || []).map((id) => byId.get(id)).filter(Boolean),
      }));
    }
    return (tutorial.steps || []).map((step, index) => ({
      group: {
        group_id: `group_${String(index + 1).padStart(2, '0')}`,
        title: (step.taxonomy_primary || '').trim() || step.step_id,
        index: index + 1,
        step_ids: [step.step_id],
      },
      steps: [step],
    }));
  }

  function isValidClip(clip) {
    return (
      clip &&
      Number.isFinite(clip.start) &&
      Number.isFinite(clip.end) &&
      clip.end > clip.start &&
      clip.start >= 0
    );
  }

  function canPlayStepClip(videoUrl, clip) {
    return Boolean(videoUrl && isValidClip(clip));
  }

  function splitDiagramPrompt(finalPrompt) {
    const text = String(finalPrompt || '').trim();
    if (!text) return { technique: '', annotation: null };
    const marker = /[，,]?\s*请在原始图片上用色块标注(?:着色范围|作用区域)/;
    const match = marker.exec(text);
    if (!match || match.index === undefined) {
      return { technique: text, annotation: null };
    }
    const technique = text.slice(0, match.index).trim();
    const annotation = text.slice(match.index).replace(/^[，,]\s*/, '').trim();
    return {
      technique: technique || text,
      annotation: annotation || null,
    };
  }

  function resolvePromptParts(item) {
    const fromBase = item.basePrompt ? splitDiagramPrompt(item.basePrompt) : null;
    const fromFinal = item.finalPrompt ? splitDiagramPrompt(item.finalPrompt) : null;
    const technique = ((fromBase && fromBase.technique) || (fromFinal && fromFinal.technique) || '').trim();
    const annotation = (fromFinal && fromFinal.annotation) || null;
    return { technique, annotation };
  }

  function hintIcon(tone) {
    if (tone === 'positive') return '✓';
    if (tone === 'adjust') return '⚙';
    return '✦';
  }

  function intensityLevels() {
    const levels = DATA.preview.intensityLevels || [];
    return levels.length
      ? levels
      : [
          { id: 'L1', color: '#ead6cf', opacity: 0.2 },
          { id: 'L2', color: '#d8aaa0', opacity: 0.4 },
          { id: 'L3', color: '#b87870', opacity: 0.6 },
          { id: 'L4', color: '#8e554f', opacity: 0.8 },
          { id: 'L5', color: '#5c3a36', opacity: 1.0 },
        ];
  }

  function activeLevel() {
    const levels = intensityLevels();
    return (
      levels.find((l) => l.id === state.intensityId) ||
      levels.find((l) => l.id === 'L4') ||
      levels[levels.length - 1]
    );
  }

  function bindNavButtons() {
    shell.querySelectorAll('[data-nav]').forEach((btn) => {
      btn.addEventListener('click', () => navigate(btn.getAttribute('data-nav')));
    });
  }

  function renderUpload() {
    const upload = DATA.upload || {};
    const fileName = upload.fileName || DATA.sources?.file_name || 'video.mp4';
    const fileSize = upload.fileSize || 0;
    const fast = (upload.parseMode || 'fast') !== 'full';
    const videoUrl = DATA.tutorial?.videoUrl || 'media/video.mp4';

    shell.className = 'mobile-shell upload-page';
    shell.innerHTML = `
      <header class="page-heading">
        <span class="demo-badge">静态演示 · 无解析</span>
        <span class="page-kicker">MAKEUP PRACTICE</span>
        <h1>上传教程</h1>
      </header>
      <button type="button" class="upload-card has-file upload-card--preview" aria-labelledby="upload-title" data-preview-full-video>
        <div class="upload-card__label">
          <span class="upload-card__icon">🎬</span>
          <span id="upload-title" class="upload-card__title">${escapeHtml(fileName)}</span>
          <span class="upload-card__meta">${escapeHtml(formatSize(fileSize))} · 点击预览完整视频</span>
        </div>
        <span class="upload-card__check" aria-hidden="true">✓</span>
      </button>
      <p class="upload-card__hint">建议视频不应过长、过大，否则无法正常解析，建议&lt;5min、大小&lt;50MB</p>
      <label class="option-row">
        <input type="checkbox" ${fast ? 'checked' : ''} disabled />
        <span class="option-row__icon">⚡</span>
        <span class="option-row__body">
          <strong>快速解析</strong>
          <small>少做一些精细检查，更快出教程</small>
        </span>
      </label>
      <section class="requirement-card" aria-labelledby="requirements-title">
        <div class="section-title-row">
          <span class="section-icon">✦</span>
          <div><span class="section-eyebrow">上传前看一眼</span><h2 id="requirements-title">视频要求</h2></div>
        </div>
        <ul class="requirement-list">
          <li>✓ 教程步骤明显</li>
          <li>✓ 人脸清晰无遮挡</li>
          <li>✓ 光线充足稳定</li>
        </ul>
      </section>
      <button class="primary-button" type="button" data-nav="photo">下一步 →</button>`;
    bindNavButtons();
    const previewBtn = shell.querySelector('[data-preview-full-video]');
    if (previewBtn) {
      previewBtn.addEventListener('click', () => {
        openClip(videoUrl, null, fileName);
      });
    }
  }

  function renderPhoto() {
    const skipped = DATA.upload?.photoSkipped !== false;
    shell.className = 'mobile-shell photo-page';
    shell.innerHTML = `
      <header class="detail-header">
        <button class="icon-button" type="button" aria-label="返回" data-nav="upload">←</button>
        <div><span class="page-kicker">STEP 02</span><h1>确认照片</h1></div>
        <span class="header-spacer"></span>
      </header>
      <div class="photo-preview" aria-label="照片预览区域">
        <div class="portrait-placeholder" aria-hidden="true">
          <span class="portrait-placeholder__halo"></span>
          <span class="portrait-placeholder__face">☺</span>
        </div>
        <span class="photo-preview__badge">${skipped ? '已跳过 · 使用标准人脸' : '上传正面照片'}</span>
      </div>
      <div class="photo-skip">
        <button class="primary-button photo-skip__button" type="button" data-nav="parsing">
          暂时跳过（使用标准人脸生成）
        </button>
        <p class="skip-explainer">本演示任务未上传自拍，预览使用平均脸底图</p>
      </div>
      <section class="photo-value-card">
        <div class="section-title-row">
          <span class="section-icon">📷</span>
          <div><span class="section-eyebrow">更贴近你的效果</span><h2>上传照片的价值</h2></div>
        </div>
        <p>我们会用照片生成更贴近你的妆后预览，并调整上妆范围与位置。</p>
        <ul class="photo-tips">
          <li><span>👤</span><div><strong>正面清晰</strong><small>保持自然表情，完整露出五官</small></div><span>✓</span></li>
          <li><span>☀</span><div><strong>光线自然</strong><small>避免强逆光或彩色灯光</small></div><span>✓</span></li>
          <li><span>🛡</span><div><strong>尽量无遮挡</strong><small>不戴口罩或大面积遮挡面部</small></div><span>✓</span></li>
        </ul>
      </section>
      <div class="privacy-note"><span>🔒</span><p>照片仅用于生成个人化预览和适配建议，你可以随时删除。</p></div>`;
    bindNavButtons();
  }

  function renderParsing() {
    const progress = DATA.progress || {
      progress: 100,
      currentStage: '整理关键建议',
      status: 'completed',
      stages: [],
      detailMessage: '[job] 完成',
    };
    const pct = Number(progress.progress) || 100;
    const stages = progress.stages || [];
    const doneCount = stages.filter((s) => s.status === 'completed').length;

    const stageList = stages
      .map((stage) => {
        const icon =
          stage.status === 'completed' ? '✓' : stage.status === 'active' ? '…' : '○';
        const label =
          stage.status === 'completed'
            ? '已完成'
            : stage.status === 'active'
              ? '处理中'
              : '等待中';
        return `
          <li class="stage-list__item is-${escapeHtml(stage.status || 'pending')}">
            <span class="stage-list__icon">${icon}</span>
            <span>${escapeHtml(stage.label)}</span>
            <small>${label}</small>
          </li>`;
      })
      .join('');

    shell.className = 'mobile-shell parsing-page';
    shell.innerHTML = `
      <header class="centered-heading">
        <span class="demo-badge">静态演示 · 已完成快照</span>
        <span class="page-kicker">AI MAKEUP ANALYSIS</span>
        <h1>解析完成</h1>
        <p>正在把教程变成适合你的上妆方案</p>
      </header>
      <section class="progress-hero" aria-label="解析进度 ${pct}%">
        <div class="progress-ring" style="--progress:${pct}">
          <div class="progress-ring__inner">
            <strong>${pct}<small>%</small></strong>
            <span>已完成</span>
          </div>
        </div>
        <div class="current-stage">
          <span>✦</span><span>当前阶段</span>
          <strong>${escapeHtml(progress.currentStage || '整理关键建议')}</strong>
        </div>
        ${
          progress.detailMessage
            ? `<p class="current-stage-detail">${escapeHtml(progress.detailMessage)}</p>`
            : ''
        }
      </section>
      <section class="stage-card" aria-labelledby="stage-title">
        <div class="section-heading">
          <h2 id="stage-title">处理步骤</h2>
          <span>${doneCount}/${stages.length || 4}</span>
        </div>
        <ol class="stage-list">${stageList}</ol>
      </section>
      <button class="primary-button" type="button" data-nav="preview">查看适配预览 →</button>`;
    bindNavButtons();
  }

  function renderPreview() {
    const preview = DATA.preview;
    const failed = Boolean(preview.generationFailed || !preview.afterImage);
    const levels = intensityLevels();
    const active = activeLevel();
    const comparison = preview.comparison;
    const aspect =
      comparison && comparison.width && comparison.height
        ? comparison.width / comparison.height
        : null;
    const objectPosition = (comparison && comparison.objectPosition) || '50% 50%';
    const opacity = active ? active.opacity : 0.8;

    const frameClass = aspect
      ? 'comparison__frame comparison__frame--sized'
      : 'comparison__frame';
    const frameStyle = aspect ? `aspect-ratio:${aspect};height:auto` : '';

    let body = '';
    if (failed) {
      body = `
        <section class="preview-generation-error" aria-label="妆容生成失败">
          <h2>妆容生成失败</h2>
          <p>${escapeHtml(preview.generationFailureReason || '妆容生成失败，暂无适配预览')}</p>
        </section>`;
    } else {
      body = `
        <section class="comparison" aria-label="妆前妆后效果对比">
          <div class="${frameClass}" style="${frameStyle}" data-slider-frame>
            <img class="comparison__image comparison__image--before" src="${escapeHtml(preview.beforeImage)}" alt="原始状态" draggable="false" style="object-position:${escapeHtml(objectPosition)}" />
            <div class="comparison__after" data-after-layer style="clip-path:inset(0 0 0 ${state.sliderPos}%);opacity:${opacity}">
              <img class="comparison__image" src="${escapeHtml(preview.afterImage)}" alt="化妆后效果" draggable="false" style="object-position:${escapeHtml(objectPosition)}" />
            </div>
            <span class="comparison__label comparison__label--before">原始状态</span>
            <span class="comparison__label comparison__label--after">化妆后</span>
            <span class="comparison__divider" data-divider style="left:${state.sliderPos}%" aria-hidden="true"><span>⟷</span></span>
            <input class="comparison__range" type="range" min="0" max="100" step="5" value="${state.sliderPos}" aria-label="妆前妆后对比位置" data-slider-range />
          </div>
          <div class="comparison__actions">
            <button type="button" data-set-pos="0">看原图</button>
            <span>拖动查看完整效果</span>
            <button type="button" data-set-pos="100">看妆后</button>
          </div>
        </section>`;
    }

    const palette = failed
      ? ''
      : `<div class="palette" role="group" aria-label="妆容浓淡">
          ${levels
            .map(
              (level) => `
            <button type="button" class="${level.id === active.id ? 'is-active' : ''}"
              style="background-color:${escapeHtml(level.color)}"
              aria-label="妆容浓淡 ${escapeHtml(level.id)}"
              aria-pressed="${level.id === active.id}"
              title="妆容浓淡 ${Math.round(level.opacity * 100)}%"
              data-intensity="${escapeHtml(level.id)}"></button>`,
            )
            .join('')}
        </div>`;

    const hints = (preview.hints || [])
      .map(
        (hint) => `
      <article class="hint-card tone-${escapeHtml(hint.tone || 'neutral')}">
        <span>${hintIcon(hint.tone)}</span>
        <div><h3>${escapeHtml(hint.title)}</h3><p>${escapeHtml(hint.description)}</p></div>
      </article>`,
      )
      .join('');

    const decision = failed
      ? ''
      : `
      <section class="decision-card" aria-label="妆容适配判断">
        <h2>这个妆适合你吗？</h2>
        <p>你的选择会帮助我们继续优化教程</p>
        <div class="decision-actions">
          <button type="button" class="is-positive" data-nav="practice">✓ 适合我</button>
          <button type="button" data-nav="adjust">⚙ 需要微调</button>
        </div>
      </section>`;

    shell.className = 'mobile-shell preview-page';
    shell.innerHTML = `
      <header class="detail-header">
        <button class="icon-button" type="button" aria-label="返回" data-nav="parsing">←</button>
        <div>
          <span class="demo-badge">静态演示 · 无解析</span>
          <span class="page-kicker">YOUR MAKEUP MATCH</span>
          <h1>适配预览</h1>
        </div>
        <span class="header-spacer"></span>
      </header>
      ${body}
      <section class="makeup-summary" aria-labelledby="summary-title">
        <div class="summary-heading">
          <div>
            <span class="section-eyebrow">解析妆容</span>
            <h2 id="summary-title">${escapeHtml(preview.title)}</h2>
          </div>
          <span class="difficulty-pill">${escapeHtml(preview.difficulty)}</span>
        </div>
        ${palette}
        <div class="summary-meta">
          <span>✦ ${escapeHtml(preview.style)}</span>
          <span>⏱ ${escapeHtml(preview.duration)}</span>
          <span>${escapeHtml(preview.occasion)}</span>
        </div>
      </section>
      <section class="adaptation-section" aria-labelledby="adapt-title">
        <div class="section-heading"><h2 id="adapt-title">关键适配提示</h2><span>为你调整</span></div>
        <div class="hint-list">${hints}</div>
      </section>
      ${decision}`;

    bindPreviewEvents();
  }

  function setSliderPos(pos) {
    state.sliderPos = Math.round(Math.min(100, Math.max(0, pos)));
    const after = shell.querySelector('[data-after-layer]');
    const divider = shell.querySelector('[data-divider]');
    const range = shell.querySelector('[data-slider-range]');
    if (after) after.style.clipPath = `inset(0 0 0 ${state.sliderPos}%)`;
    if (divider) divider.style.left = `${state.sliderPos}%`;
    if (range) range.value = String(state.sliderPos);
  }

  function bindPreviewEvents() {
    const frame = shell.querySelector('[data-slider-frame]');
    if (frame) {
      const updateFromClientX = (clientX) => {
        const bounds = frame.getBoundingClientRect();
        if (!bounds.width) return;
        setSliderPos(((clientX - bounds.left) / bounds.width) * 100);
      };
      frame.addEventListener('pointerdown', (event) => {
        frame.setPointerCapture?.(event.pointerId);
        updateFromClientX(event.clientX);
      });
      frame.addEventListener('pointermove', (event) => {
        if (frame.hasPointerCapture?.(event.pointerId)) updateFromClientX(event.clientX);
      });
    }

    const range = shell.querySelector('[data-slider-range]');
    if (range) {
      range.addEventListener('input', () => setSliderPos(Number(range.value)));
      range.addEventListener('keydown', (event) => {
        if (event.key === 'ArrowRight' || event.key === 'ArrowUp') {
          event.preventDefault();
          setSliderPos(state.sliderPos + 5);
        } else if (event.key === 'ArrowLeft' || event.key === 'ArrowDown') {
          event.preventDefault();
          setSliderPos(state.sliderPos - 5);
        } else if (event.key === 'Home') {
          event.preventDefault();
          setSliderPos(0);
        } else if (event.key === 'End') {
          event.preventDefault();
          setSliderPos(100);
        }
      });
    }

    shell.querySelectorAll('[data-set-pos]').forEach((btn) => {
      btn.addEventListener('click', () => setSliderPos(Number(btn.getAttribute('data-set-pos'))));
    });

    shell.querySelectorAll('[data-intensity]').forEach((btn) => {
      btn.addEventListener('click', () => {
        state.intensityId = btn.getAttribute('data-intensity') || 'L4';
        const level = activeLevel();
        const after = shell.querySelector('[data-after-layer]');
        if (after && level) after.style.opacity = String(level.opacity);
        shell.querySelectorAll('[data-intensity]').forEach((el) => {
          const on = el.getAttribute('data-intensity') === state.intensityId;
          el.classList.toggle('is-active', on);
          el.setAttribute('aria-pressed', String(on));
        });
      });
    });

    bindNavButtons();
  }

  function renderPractice() {
    const tutorial = DATA.tutorial;
    const groups = resolveTutorialGroups(tutorial);
    const videoUrl = tutorial.videoUrl || '';

    const list = groups
      .map(({ group, steps }) => {
        const multi = steps.length > 1;
        const segments = steps
          .map((step) => {
            const playable = canPlayStepClip(videoUrl, step.video_clip);
            const title = multi
              ? `${groupHeading(group)} · ${stepSegmentTitle(step)}`
              : groupHeading(group);
            return `
              <div class="tutorial-step-segment">
                ${multi ? `<h4 class="tutorial-step-segment__title">${escapeHtml(stepSegmentTitle(step))}</h4>` : ''}
                <dl class="tutorial-step-fields">
                  <div><dt>产品</dt><dd>${escapeHtml(formatProductLine(step))}</dd></div>
                  <div><dt>范围</dt><dd>${escapeHtml(formatRangeText(step))}</dd></div>
                  <div><dt>手法</dt><dd>${escapeHtml(formatTechnique(step))}</dd></div>
                </dl>
                <button class="step-clip-trigger" type="button" ${playable ? '' : 'disabled'}
                  data-play-clip="${escapeHtml(step.step_id)}"
                  data-clip-title="${escapeHtml(title)}">
                  ▶ 看视频
                </button>
              </div>`;
          })
          .join('');
        return `
          <li class="tutorial-step-card">
            <h3>${escapeHtml(groupHeading(group))}</h3>
            <div class="tutorial-step-segments">${segments}</div>
          </li>`;
      })
      .join('');

    shell.className = 'mobile-shell practice-page';
    shell.innerHTML = `
      <header class="detail-header">
        <button class="icon-button" type="button" aria-label="返回" data-nav="preview">←</button>
        <div>
          <span class="page-kicker">FOLLOW ALONG</span>
          <h1>跟练教程</h1>
        </div>
        <span class="header-spacer"></span>
      </header>
      <section class="makeup-summary" aria-labelledby="tutorial-title">
        <div class="summary-heading">
          <div>
            <span class="section-eyebrow">视频解读</span>
            <h2 id="tutorial-title">${escapeHtml(tutorial.title || DATA.preview.title || '跟练教程')}</h2>
          </div>
        </div>
        <p class="tutorial-intro">按视频步骤使用对应产品、范围与手法跟练。</p>
      </section>
      <ol class="tutorial-step-list" aria-label="教程步骤">${list}</ol>
      ${
        PAGES.some((p) => p.id === 'examples')
          ? `<section class="practice-footer" aria-label="跟练下一步">
              <button class="primary-button practice-footer__cta" type="button" data-nav="examples">
                前往示例图 →
              </button>
            </section>`
          : ''
      }`;

    bindNavButtons();

    const byId = new Map((tutorial.steps || []).map((s) => [s.step_id, s]));
    shell.querySelectorAll('[data-play-clip]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const step = byId.get(btn.getAttribute('data-play-clip'));
        if (!step) return;
        openClip(videoUrl, step.video_clip, btn.getAttribute('data-clip-title') || '');
      });
    });
  }

  function renderExamples() {
    const doc = DATA.stepDiagrams;
    if (!doc || !doc.steps || !doc.steps.length) {
      shell.className = 'mobile-shell practice-page';
      shell.innerHTML = `
        <header class="detail-header">
          <button class="icon-button" type="button" aria-label="返回" data-nav="practice">←</button>
          <div><span class="page-kicker">STEP DIAGRAMS</span><h1>步骤示例图</h1></div>
          <span class="header-spacer"></span>
        </header>
        <p class="tutorial-intro">暂无示例图数据，请重新导出 demo。</p>`;
      bindNavButtons();
      return;
    }

    const steps = [...doc.steps].sort((a, b) => (a.index || 0) - (b.index || 0));
    const videoUrl = doc.videoUrl || DATA.tutorial.videoUrl || '';
    const collecting = state.collectMode;
    const selected = new Set(state.selectedStepIds);

    const cards = steps
      .map((item) => {
        const playable = canPlayStepClip(videoUrl, item.videoClip);
        const { technique, annotation } = resolvePromptParts(item);
        const media = item.imageUrl
          ? `<img src="${escapeHtml(item.imageUrl)}" alt="${escapeHtml(item.heading)} 着色范围示意" loading="lazy" />`
          : `<div class="diagram-card__placeholder${item.status === 'failed' ? ' is-error' : ''}">
              <span>${item.status === 'failed' ? '生成失败' : '暂无图示'}</span>
              ${item.error ? `<p class="diagram-card__error">${escapeHtml(item.error)}</p>` : ''}
            </div>`;
        return `
          <li class="diagram-card" id="diagram-step-${escapeHtml(item.stepId)}" data-step-id="${escapeHtml(item.stepId)}">
            <h2>${escapeHtml(item.heading)}</h2>
            <div class="diagram-card__media">${media}</div>
            ${technique ? `<p class="diagram-card__technique">${escapeHtml(technique)}</p>` : ''}
            ${
              annotation
                ? `<details class="diagram-card__prompt"><summary>标注说明</summary><p>${escapeHtml(annotation)}</p></details>`
                : ''
            }
            <button class="step-clip-trigger" type="button" ${playable ? '' : 'disabled'}
              data-play-example="${escapeHtml(item.stepId)}"
              data-clip-title="${escapeHtml(item.heading)}">
              ▶ 看视频
            </button>
          </li>`;
      })
      .join('');

    const indexBtns = steps
      .map((item, i) => {
        const name = String(item.heading || '').split(' · ').slice(1).join(' · ') || item.stepId;
        const isSelected = selected.has(item.stepId);
        return `<button type="button"
          class="diagram-step-index__btn${isSelected ? ' is-selected' : ''}"
          data-index-step="${escapeHtml(item.stepId)}"
          aria-pressed="${collecting ? String(isSelected) : 'false'}"
          aria-label="${collecting ? '勾选' : '跳转到'}步骤 ${i + 1} ${escapeHtml(name)}">
          <span class="diagram-step-index__num">${collecting && isSelected ? '✓' : i + 1}</span>
          <span class="diagram-step-index__name">${escapeHtml(name)}</span>
        </button>`;
      })
      .join('');

    shell.className = `mobile-shell practice-page diagram-gallery-page${collecting ? ' is-collecting' : ''}`;
    shell.innerHTML = `
      <header class="detail-header" id="diagram-gallery-top">
        <button class="icon-button" type="button"
          aria-label="${collecting ? '退出勾选' : '返回跟练'}"
          data-examples-back>${collecting ? '×' : '←'}</button>
        <div>
          <span class="page-kicker">STEP DIAGRAMS</span>
          <h1>步骤示例图</h1>
        </div>
        <span class="header-spacer"></span>
      </header>
      ${doc.failureReason ? `<section class="analysis-error" role="alert"><p>${escapeHtml(doc.failureReason)}</p></section>` : ''}
      ${collecting ? '<p class="diagram-progress-banner" role="status">勾选要收藏到知识库的步骤</p>' : ''}
      <div class="diagram-gallery-layout">
        <ul class="diagram-gallery" aria-label="步骤示例图列表">${cards}</ul>
        <nav class="diagram-step-index${collecting ? ' is-collecting' : ''}" aria-label="步骤索引">
          <div class="diagram-step-index__list">${indexBtns}</div>
          ${
            collecting
              ? '<button type="button" class="diagram-step-index__top" data-select-all>勾选全部</button>'
              : '<button type="button" class="diagram-step-index__top" data-scroll-top>↑ 顶部</button>'
          }
        </nav>
      </div>
      <section class="practice-footer diagram-collect-footer" aria-label="收藏操作">
        ${
          collecting
            ? `<button class="primary-button practice-footer__cta" type="button" data-confirm-collect
                ${state.selectedStepIds.length === 0 ? 'disabled' : ''}>
                勾选完成${state.selectedStepIds.length ? `（${state.selectedStepIds.length}）` : ''}
              </button>`
            : `<button class="primary-button practice-footer__cta" type="button" data-enter-collect>
                收藏到知识库
              </button>`
        }
      </section>`;

    const byId = new Map(steps.map((s) => [s.stepId, s]));
    shell.querySelectorAll('[data-play-example]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const item = byId.get(btn.getAttribute('data-play-example'));
        if (!item) return;
        openClip(videoUrl, item.videoClip, btn.getAttribute('data-clip-title') || '');
      });
    });

    const backBtn = shell.querySelector('[data-examples-back]');
    if (backBtn) {
      backBtn.addEventListener('click', () => {
        if (state.collectMode) {
          state.collectMode = false;
          state.selectedStepIds = [];
          renderExamples();
          updatePager();
          return;
        }
        navigate('practice');
      });
    }

    shell.querySelectorAll('[data-index-step]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const id = btn.getAttribute('data-index-step');
        if (!id) return;
        if (state.collectMode) {
          if (state.selectedStepIds.includes(id)) {
            state.selectedStepIds = state.selectedStepIds.filter((x) => x !== id);
          } else {
            state.selectedStepIds = [...state.selectedStepIds, id];
          }
          const node = document.getElementById(`diagram-step-${id}`);
          if (node) node.scrollIntoView({ behavior: 'smooth', block: 'start' });
          renderExamples();
          updatePager();
          return;
        }
        const node = document.getElementById(`diagram-step-${id}`);
        if (node) node.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });

    const topBtn = shell.querySelector('[data-scroll-top]');
    if (topBtn) {
      topBtn.addEventListener('click', () => {
        const top = document.getElementById('diagram-gallery-top');
        if (top) top.scrollIntoView({ behavior: 'smooth', block: 'start' });
        else shell.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }

    const selectAllBtn = shell.querySelector('[data-select-all]');
    if (selectAllBtn) {
      selectAllBtn.addEventListener('click', () => {
        state.selectedStepIds = steps.map((s) => s.stepId);
        renderExamples();
        updatePager();
      });
    }

    const enterCollect = shell.querySelector('[data-enter-collect]');
    if (enterCollect) {
      enterCollect.addEventListener('click', () => {
        state.collectMode = true;
        state.selectedStepIds = [];
        renderExamples();
        updatePager();
      });
    }

    const confirmCollect = shell.querySelector('[data-confirm-collect]');
    if (confirmCollect) {
      confirmCollect.addEventListener('click', () => {
        if (!state.selectedStepIds.length) return;
        navigate('collected');
      });
    }
  }

  function renderCollected() {
    const count = state.selectedStepIds.length;
    shell.className = 'mobile-shell practice-page collect-success-page';
    shell.innerHTML = `
      <header class="detail-header">
        <button class="icon-button" type="button" aria-label="返回" data-nav="examples">←</button>
        <div>
          <span class="page-kicker">LIBRARY</span>
          <h1>收藏结果</h1>
        </div>
        <span class="header-spacer"></span>
      </header>
      <div class="collect-success">
        <div class="collect-success__icon" aria-hidden="true">📚</div>
        <h2>收藏成功！</h2>
        <p class="collect-success__meta">已勾选 ${count} 个步骤加入知识库（演示模式，未实际上传）</p>
        <button class="primary-button practice-footer__cta" type="button" data-nav="examples">
          返回示例图
        </button>
      </div>`;
    bindNavButtons();
  }

  function closeClip() {
    if (clipCleanup) {
      clipCleanup();
      clipCleanup = null;
    }
    overlay.hidden = true;
    overlay.innerHTML = '';
    state.clip = null;
  }

  function openClip(videoUrl, clip, title) {
    const limited = isValidClip(clip) ? clip : null;
    state.clip = { videoUrl, clip: limited, title };
    overlay.hidden = false;
    overlay.innerHTML = `
      <div class="step-clip-panel">
        <header class="step-clip-panel__header">
          <h2>${escapeHtml(title || '步骤视频')}</h2>
          <button class="icon-button" type="button" aria-label="关闭视频" data-close-clip>×</button>
        </header>
        <video class="step-clip-panel__video" src="${escapeHtml(videoUrl)}" controls playsinline preload="metadata"></video>
      </div>`;

    const video = overlay.querySelector('video');
    const closeBtn = overlay.querySelector('[data-close-clip]');

    const onKeyDown = (event) => {
      if (event.key === 'Escape') closeClip();
    };
    const onOverlayClick = (event) => {
      if (event.target === overlay) closeClip();
    };
    closeBtn.addEventListener('click', closeClip);
    window.addEventListener('keydown', onKeyDown);
    overlay.addEventListener('click', onOverlayClick);

    const seekAndPlay = () => {
      if (limited) {
        try {
          video.currentTime = limited.start;
        } catch {
          /* ignore */
        }
      }
      void video.play().catch(() => {});
    };
    const onTimeUpdate = () => {
      if (!limited) return;
      if (video.currentTime >= limited.end) {
        video.pause();
        try {
          video.currentTime = limited.end;
        } catch {
          /* ignore */
        }
      }
    };
    const onLoadedMetadata = () => seekAndPlay();

    video.addEventListener('timeupdate', onTimeUpdate);
    video.addEventListener('loadedmetadata', onLoadedMetadata);
    if (video.readyState >= 1) seekAndPlay();

    clipCleanup = () => {
      window.removeEventListener('keydown', onKeyDown);
      overlay.removeEventListener('click', onOverlayClick);
      video.removeEventListener('timeupdate', onTimeUpdate);
      video.removeEventListener('loadedmetadata', onLoadedMetadata);
      video.pause();
    };
  }

  function chipHtml(name, value, selected, type) {
    const on = selected;
    return `
      <label class="choice-chip${on ? ' is-selected' : ''}">
        <input type="${type}" name="${escapeHtml(name)}" value="${escapeHtml(value)}" ${on ? 'checked' : ''} />
        <span>${escapeHtml(value)}</span>${on ? ' ✓' : ''}
      </label>`;
  }

  function renderAdjust() {
    const a = state.adjust;
    shell.className = 'mobile-shell adjust-page';
    shell.innerHTML = `
      <header class="detail-header">
        <button class="icon-button" type="button" aria-label="返回" data-nav="preview">←</button>
        <div><span class="page-kicker">PERSONALIZE</span><h1>微调设置</h1></div>
        <span class="header-spacer"></span>
      </header>
      <div class="adjust-intro"><p>告诉我们你想怎么调整，我们会改写范围、颜色、位置、工具和顺序。（演示模式不会调用优化接口）</p></div>
      <form class="adjust-form" id="adjust-form">
        <fieldset class="choice-section">
          <div class="choice-section__heading"><h2>个人风格</h2></div>
          <div class="choice-question">
            <h3>你希望这个妆容更偏向哪种风格？</h3><small>单选</small>
            <div class="choice-grid" data-field="style">
              ${STYLE_OPTIONS.map((item) => chipHtml('styles', item, a.style === item, 'radio')).join('')}
            </div>
          </div>
          <div class="choice-question">
            <h3>这个妆主要使用在哪些场景？</h3><small>多选</small>
            <div class="choice-grid" data-field="occasions">
              ${OCCASION_OPTIONS.map((item) =>
                chipHtml('occasions', item, a.occasions.includes(item), 'checkbox'),
              ).join('')}
            </div>
          </div>
        </fieldset>
        <fieldset class="choice-section">
          <div class="choice-section__heading"><h2>脸部匹配</h2></div>
          <div class="choice-question">
            <h3>你希望保留原教程的哪些部分？</h3><small>多选</small>
            <div class="choice-grid" data-field="retainedParts">
              ${RETAINED_PART_OPTIONS.map((item) =>
                chipHtml('retainedParts', item, a.retainedParts.includes(item), 'checkbox'),
              ).join('')}
            </div>
          </div>
          <div class="choice-question">
            <h3>你的肤质更接近哪种？</h3><small>单选</small>
            <div class="choice-grid" data-field="skinType">
              ${SKIN_TYPE_OPTIONS.map((item) =>
                chipHtml('skinType', item, a.skinType === item, 'radio'),
              ).join('')}
            </div>
          </div>
          <div class="choice-question">
            <h3>你希望通过化妆修饰什么问题？</h3><small>多选</small>
            <div class="choice-grid" data-field="concerns">
              ${CONCERN_OPTIONS.map((item) =>
                chipHtml('concerns', item, a.concerns.includes(item), 'checkbox'),
              ).join('')}
            </div>
          </div>
        </fieldset>
        <fieldset class="choice-section">
          <div class="choice-section__heading"><h2>工具</h2></div>
          <div class="choice-question">
            <h3>你有哪些限制？</h3><small>多选</small>
            <div class="choice-grid" data-field="constraints">
              ${CONSTRAINT_OPTIONS.map((item) =>
                chipHtml('constraints', item, a.constraints.includes(item), 'checkbox'),
              ).join('')}
            </div>
          </div>
        </fieldset>
        <button class="primary-button" type="submit">生成方案 →</button>
      </form>`;

    bindNavButtons();

    const bindSingle = (field) => {
      shell.querySelectorAll(`[data-field="${field}"] input`).forEach((input) => {
        input.addEventListener('change', () => {
          state.adjust[field] = input.value;
          renderAdjust();
          updatePager();
        });
      });
    };
    const bindMulti = (field) => {
      shell.querySelectorAll(`[data-field="${field}"] input`).forEach((input) => {
        input.addEventListener('change', () => {
          const list = state.adjust[field];
          if (input.checked) {
            if (!list.includes(input.value)) list.push(input.value);
          } else {
            state.adjust[field] = list.filter((v) => v !== input.value);
          }
          renderAdjust();
          updatePager();
        });
      });
    };

    bindSingle('style');
    bindSingle('skinType');
    bindMulti('occasions');
    bindMulti('retainedParts');
    bindMulti('concerns');
    bindMulti('constraints');

    shell.querySelector('#adjust-form').addEventListener('submit', (event) => {
      event.preventDefault();
      showToast('演示模式已记录，未调用优化接口');
      navigate('practice');
    });
  }

  function render() {
    if (state.route === 'upload') renderUpload();
    else if (state.route === 'photo') renderPhoto();
    else if (state.route === 'parsing') renderParsing();
    else if (state.route === 'practice') renderPractice();
    else if (state.route === 'examples') renderExamples();
    else if (state.route === 'collected') renderCollected();
    else if (state.route === 'adjust') renderAdjust();
    else renderPreview();
    shell.scrollTop = 0;
    updatePager();
  }

  if (pagerPrev) pagerPrev.addEventListener('click', () => goRelative(-1));
  if (pagerNext) pagerNext.addEventListener('click', () => goRelative(1));

  window.addEventListener('keydown', (event) => {
    if (!overlay.hidden) return;
    const tag = (event.target && event.target.tagName) || '';
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
    if (event.key === 'ArrowLeft') {
      event.preventDefault();
      goRelative(-1);
    } else if (event.key === 'ArrowRight') {
      event.preventDefault();
      goRelative(1);
    }
  });

  window.addEventListener('hashchange', () => {
    state.route = readHash();
    render();
  });

  state.route = readHash();
  if (!window.location.hash) window.location.hash = 'upload';
  render();
})();
