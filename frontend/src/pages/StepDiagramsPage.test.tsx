import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';
import { CollectSuccessPage } from './CollectSuccessPage';
import { StepDiagramsPage } from './StepDiagramsPage';

beforeEach(() => {
  class MockIntersectionObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
    takeRecords() {
      return [];
    }
  }
  vi.stubGlobal('IntersectionObserver', MockIntersectionObserver);
});

test('renders diagram steps with watch-video buttons', async () => {
  sessionStorage.setItem('makeupTask', JSON.stringify({ taskId: 'task-diagrams' }));
  render(
    <MemoryRouter>
      <StepDiagramsPage />
    </MemoryRouter>,
  );

  expect(await screen.findByRole('heading', { name: '步骤示例图' })).toBeInTheDocument();
  await waitFor(() => {
    expect(screen.getAllByRole('button', { name: '看视频' }).length).toBeGreaterThan(0);
  });
});

test('renders ordered step index with names, jump, and back-to-top', async () => {
  const user = userEvent.setup();
  sessionStorage.setItem('makeupTask', JSON.stringify({ taskId: 'task-diagrams' }));
  render(
    <MemoryRouter>
      <StepDiagramsPage />
    </MemoryRouter>,
  );

  const indexNav = await screen.findByRole('navigation', { name: '步骤索引' });
  const stepButtons = await waitFor(() => {
    const buttons = Array.from(indexNav.querySelectorAll('.diagram-step-index__btn'));
    expect(buttons.length).toBeGreaterThanOrEqual(2);
    return buttons as HTMLButtonElement[];
  });

  expect(stepButtons.map((btn) => btn.querySelector('.diagram-step-index__num')?.textContent)).toEqual(
    stepButtons.map((_, i) => String(i + 1)),
  );
  expect(stepButtons[0].querySelector('.diagram-step-index__name')?.textContent).toBeTruthy();
  expect(screen.getByRole('button', { name: '回到顶部' })).toBeInTheDocument();

  const secondCard = document.getElementById('diagram-step-blush_01');
  expect(secondCard).toBeTruthy();
  const scrollIntoView = vi.fn();
  Object.defineProperty(secondCard, 'scrollIntoView', {
    configurable: true,
    value: scrollIntoView,
  });

  const secondButton = screen.getByRole('button', { name: /跳转到步骤 2/ });
  await user.click(secondButton);
  expect(scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth', block: 'start' });
  expect(secondButton).toHaveAttribute('aria-current', 'true');

  const topTarget = document.getElementById('diagram-gallery-top');
  expect(topTarget).toBeTruthy();
  const scrollTop = vi.fn();
  Object.defineProperty(topTarget, 'scrollIntoView', {
    configurable: true,
    value: scrollTop,
  });
  await user.click(screen.getByRole('button', { name: '回到顶部' }));
  expect(scrollTop).toHaveBeenCalledWith({ behavior: 'smooth', block: 'start' });
});

test('collect mode selects steps and navigates to success page', async () => {
  const user = userEvent.setup();
  sessionStorage.setItem('makeupTask', JSON.stringify({ taskId: 'task-diagrams' }));
  render(
    <MemoryRouter initialEntries={['/practice/examples']}>
      <Routes>
        <Route path="/practice/examples" element={<StepDiagramsPage />} />
        <Route path="/practice/examples/saved" element={<CollectSuccessPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByRole('button', { name: '收藏到知识库' })).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '收藏到知识库' }));

  expect(screen.getByRole('button', { name: '勾选全部' })).toBeInTheDocument();
  const confirmButton = screen.getByRole('button', { name: '勾选完成' });
  expect(confirmButton).toBeDisabled();

  const firstStep = screen.getByRole('button', { name: /勾选步骤 1/ });
  await user.click(firstStep);
  expect(firstStep).toHaveAttribute('aria-pressed', 'true');
  expect(confirmButton).toBeEnabled();

  await user.click(screen.getByRole('button', { name: '勾选全部' }));
  const selectedButtons = screen.getAllByRole('button', { name: /勾选步骤/ });
  for (const button of selectedButtons) {
    expect(button).toHaveAttribute('aria-pressed', 'true');
  }

  await user.click(confirmButton);
  expect(await screen.findByRole('heading', { name: '收藏成功！' })).toBeInTheDocument();
});
