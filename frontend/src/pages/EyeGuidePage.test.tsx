import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { EyeGuidePage } from './EyeGuidePage';

test('updates guidance when an eye region is selected', async () => {
  const user = userEvent.setup();
  render(<MemoryRouter><EyeGuidePage /></MemoryRouter>);

  await user.click(await screen.findByRole('button', { name: '眼线走势' }));

  expect(screen.getByText(/眼尾向外延伸/)).toBeInTheDocument();
});
