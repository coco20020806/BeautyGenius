import { Route, Routes } from 'react-router-dom';
import { PlaceholderPage } from './pages/PlaceholderPage';
import { PhotoPage } from './pages/PhotoPage';
import { ParsingPage } from './pages/ParsingPage';
import { PracticePage } from './pages/PracticePage';
import { StepDiagramsPage } from './pages/StepDiagramsPage';
import { PreviewPage } from './pages/PreviewPage';
import { UploadPage } from './pages/UploadPage';

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<UploadPage />} />
      <Route path="/photo" element={<PhotoPage />} />
      <Route path="/parsing" element={<ParsingPage />} />
      <Route path="/preview" element={<PreviewPage />} />
      <Route path="/practice" element={<PracticePage />} />
      <Route path="/practice/examples" element={<StepDiagramsPage />} />
      <Route path="/library" element={<PlaceholderPage title="知识库" />} />
      <Route path="/profile" element={<PlaceholderPage title="我的" />} />
    </Routes>
  );
}

export default function App() {
  return <AppRoutes />;
}
