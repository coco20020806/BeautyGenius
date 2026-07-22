import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ProfilePage } from './ProfilePage';

test('shows preference style as static profile information', () => {
  render(<MemoryRouter><ProfilePage /></MemoryRouter>);

  expect(screen.getByText('MY BEAUTY PROFILE')).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: '我的' })).not.toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: '最近收藏' })).not.toBeInTheDocument();
  expect(screen.queryByText('清透玫瑰通勤妆')).not.toBeInTheDocument();
  expect(screen.getByText('偏好风格')).toBeInTheDocument();
  expect(screen.getByText('清透自然')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /偏好风格/ })).not.toBeInTheDocument();
  expect(screen.queryByRole('listbox', { name: '选择偏好风格' })).not.toBeInTheDocument();
});
