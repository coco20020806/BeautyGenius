import css from './global.css?raw';
import learningCss from './learning.css?raw';

test('adapts the phone canvas across mobile viewport sizes with internal scrolling', () => {
  expect(css).toContain('--phone-min-width: 320px');
  expect(css).toContain('--phone-max-width: 440px');
  expect(css).toMatch(/width:\s*clamp\(var\(--phone-min-width\),\s*100vw,\s*var\(--phone-max-width\)\)/);
  expect(css).toMatch(/height:\s*100dvh/);
  expect(css).toMatch(/body\s*\{[^}]*overflow:\s*hidden/);
  expect(css).toMatch(/\.mobile-shell\s*\{[^}]*overflow-y:\s*auto/);
  expect(css).toMatch(/\.bottom-nav\s*\{[^}]*position:\s*fixed/);
  expect(css).toMatch(/\.home-exit-button\s*\{[^}]*position:\s*fixed/);
});

test('uses the provided bitmap assets as page backgrounds', () => {
  expect(css).toContain("url('../assets/bg-home-collage.png')");
  expect(css).toContain("url('../assets/bg-photo-flower.png')");
  expect(css).toContain("url('../assets/bg-analysis-lilies.png')");
  expect(css).toContain("url('../assets/bg-custom-paper.png')");
  expect(learningCss).toContain("url('../assets/bg-library-flower.png')");
});

test('keeps the library tabs long and slim beside the filter button', () => {
  expect(learningCss).toMatch(/\.library-tab-row\s*\{[^}]*grid-template-columns:\s*minmax\(0,1fr\)\s+44px/);
  expect(learningCss).toMatch(/\.library-tabs\s*\{[^}]*padding:\s*3px/);
  expect(learningCss).toMatch(/\.library-tabs button\s*\{[^}]*min-height:\s*38px/);
  expect(learningCss).toMatch(/\.filter-scroll button\.is-full-face\s*\{[^}]*background:\s*#c8dfc3/);
  expect(learningCss).toMatch(/\.asset-card__visual\.is-empty/);
});
