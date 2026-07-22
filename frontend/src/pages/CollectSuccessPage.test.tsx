import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, test } from 'vitest';
import { CollectSuccessPage } from './CollectSuccessPage';

test('shows collect success message', () => {
  render(
    <MemoryRouter>
      <CollectSuccessPage />
    </MemoryRouter>,
  );

  expect(screen.getByRole('heading', { name: '收藏成功！' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '返回示例图' })).toBeInTheDocument();
});
