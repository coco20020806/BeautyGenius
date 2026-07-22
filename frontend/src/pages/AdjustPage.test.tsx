import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AdjustPage } from './AdjustPage';

test('submits selected adjustment and opens tutorial', async () => {
  const user = userEvent.setup();
  render(
    <MemoryRouter initialEntries={['/adjust']}>
      <Routes>
        <Route path="/adjust" element={<AdjustPage />} />
        <Route path="/tutorial" element={<h1>图示教程</h1>} />
      </Routes>
    </MemoryRouter>,
  );

  expect(screen.getByRole('group', { name: /个人风格/ })).toBeInTheDocument();
  expect(screen.getByRole('group', { name: /脸部匹配/ })).toBeInTheDocument();
  expect(screen.getByRole('group', { name: /工具/ })).toBeInTheDocument();
  expect(screen.queryByLabelText('补充要求')).not.toBeInTheDocument();

  await user.click(screen.getByRole('checkbox', { name: '清透自然' }));
  await user.click(screen.getByRole('checkbox', { name: '清冷高级' }));
  await user.click(screen.getByRole('checkbox', { name: '通勤工作' }));
  await user.click(screen.getByRole('checkbox', { name: '眼妆' }));
  await user.click(screen.getByRole('radio', { name: '敏感肌' }));
  await user.click(screen.getByRole('checkbox', { name: '放大眼睛' }));
  await user.click(screen.getByRole('checkbox', { name: '没有专业刷具' }));
  await user.click(screen.getByRole('button', { name: '生成方案' }));

  expect(await screen.findByRole('heading', { name: '图示教程' })).toBeInTheDocument();
}, 15000);

test('removes the previous adjustment questions', () => {
  render(<MemoryRouter><AdjustPage /></MemoryRouter>);

  expect(screen.getByText('个人风格').closest('fieldset')).toBeInTheDocument();
  expect(screen.getByText('脸部匹配').closest('fieldset')).toBeInTheDocument();
  expect(screen.getByText('工具').closest('fieldset')).toBeInTheDocument();
  expect(screen.queryByText('选择妆容方向与使用场景')).not.toBeInTheDocument();
  expect(screen.queryByText('结合肤质与修饰目标调整步骤')).not.toBeInTheDocument();
  expect(screen.queryByText('我们会据此简化工具与步骤')).not.toBeInTheDocument();
  expect(screen.queryByText('适配场合')).not.toBeInTheDocument();
  expect(screen.queryByText('执行工具')).not.toBeInTheDocument();
  expect(screen.queryByText('自由文本')).not.toBeInTheDocument();
});
