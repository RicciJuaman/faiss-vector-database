import { render, screen } from '@testing-library/react';
import App from './App';

test('renders hybrid search interface', () => {
  render(<App />);

  expect(screen.getByRole('heading', { name: /find the best matches/i })).toBeInTheDocument();
  expect(screen.getByPlaceholderText(/search for reviews, products, or topics/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
});
