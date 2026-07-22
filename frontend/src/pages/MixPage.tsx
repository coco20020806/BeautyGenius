import { Navigate, useLocation } from 'react-router-dom';

export function MixPage() {
  const location = useLocation();
  return <Navigate to={`/library?tab=mix${location.search ? `&${location.search.slice(1)}` : ''}`} replace />;
}
