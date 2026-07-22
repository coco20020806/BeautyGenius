import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppRoutes } from './App';

test('renders the upload screen at the root route', () => {
  render(
    <MemoryRouter initialEntries={['/']}>
      <AppRoutes />
    </MemoryRouter>,
  );

  expect(screen.getByRole('heading', { name: '上传教程' })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /回到首页/ })).not.toBeInTheDocument();
});

test('shows a fixed home exit button on non-home routes', () => {
  render(
    <MemoryRouter initialEntries={['/preview']}>
      <AppRoutes />
    </MemoryRouter>,
  );

  expect(screen.getByRole('button', { name: /回到首页/ })).toBeInTheDocument();
});
