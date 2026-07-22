import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';
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

test('renders ordered step index and jumps on click', async () => {
  const user = userEvent.setup();
  sessionStorage.setItem('makeupTask', JSON.stringify({ taskId: 'task-diagrams' }));
  render(
    <MemoryRouter>
      <StepDiagramsPage />
    </MemoryRouter>,
  );

  const indexNav = await screen.findByRole('navigation', { name: '步骤索引' });
  await waitFor(() => {
    expect(indexNav.querySelectorAll('button').length).toBeGreaterThanOrEqual(2);
  });

  const indexButtons = Array.from(indexNav.querySelectorAll('button'));
  expect(indexButtons.map((btn) => btn.textContent)).toEqual(
    indexButtons.map((_, i) => String(i + 1)),
  );

  const secondCard = document.getElementById('diagram-step-blush_01');
  expect(secondCard).toBeTruthy();
  const scrollIntoView = vi.fn();
  Object.defineProperty(secondCard, 'scrollIntoView', {
    configurable: true,
    value: scrollIntoView,
  });

  const secondButton = screen.getByRole('button', { name: '跳转到步骤 2' });
  await user.click(secondButton);

  expect(scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth', block: 'start' });
  expect(secondButton).toHaveAttribute('aria-current', 'true');
});
