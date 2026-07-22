import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { learningService } from '../services/learningService';
import { MixPreviewPage } from './MixPreviewPage';

function Target({ title }: { title: string }) {
  const location = useLocation();
  return <h1>{title}<span>{JSON.stringify(location.state)}</span></h1>;
}

test('shows preset comparison and opens its tutorial when suitable', async () => {
  const user = userEvent.setup();
  const result = await learningService.generateMix({ base: null, eyes: 'eyes-rose', blush: null, contour: null, lips: null });
  render(<MemoryRouter initialEntries={[{ pathname: '/mix/preview', state: { resultId: result.id } }]}><Routes><Route path="/mix/preview" element={<MixPreviewPage />} /><Route path="/tutorial" element={<Target title="图示教程" />} /></Routes></MemoryRouter>);

  expect(await screen.findByRole('region', { name: '妆前妆后效果对比' })).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: '适合我' }));
  expect(screen.getByRole('heading', { name: /图示教程/ })).toHaveTextContent(result.tutorialId);
});

test('sends the preset tutorial context into adjustment', async () => {
  const user = userEvent.setup();
  const result = await learningService.generateMix({ base: null, eyes: null, blush: null, contour: null, lips: 'lips-rose' });
  render(<MemoryRouter initialEntries={[{ pathname: '/mix/preview', state: { resultId: result.id } }]}><Routes><Route path="/mix/preview" element={<MixPreviewPage />} /><Route path="/adjust" element={<Target title="微调设置" />} /></Routes></MemoryRouter>);

  await user.click(await screen.findByRole('button', { name: '需要微调' }));
  expect(screen.getByRole('heading', { name: /微调设置/ })).toHaveTextContent(result.tutorialId);
});
