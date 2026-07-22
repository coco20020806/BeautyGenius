import { Route, Routes } from 'react-router-dom';
import { PhotoPage } from './pages/PhotoPage';
import { ParsingPage } from './pages/ParsingPage';
import { PracticePage } from './pages/PracticePage';
import { StepDiagramsPage } from './pages/StepDiagramsPage';
import { CollectSuccessPage } from './pages/CollectSuccessPage';
import { PreviewPage } from './pages/PreviewPage';
import { UploadPage } from './pages/UploadPage';
import { AdjustPage } from './pages/AdjustPage';
import { EyeGuidePage } from './pages/EyeGuidePage';
import { LibraryPage } from './pages/LibraryPage';
import { MixPage } from './pages/MixPage';
import { MixGeneratingPage } from './pages/MixGeneratingPage';
import { MixPreviewPage } from './pages/MixPreviewPage';
import { ProfilePage } from './pages/ProfilePage';
import { TutorialPage } from './pages/TutorialPage';

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<UploadPage />} />
      <Route path="/photo" element={<PhotoPage />} />
      <Route path="/parsing" element={<ParsingPage />} />
      <Route path="/preview" element={<PreviewPage />} />
      <Route path="/practice" element={<PracticePage />} />
      <Route path="/practice/examples" element={<StepDiagramsPage />} />
      <Route path="/practice/examples/saved" element={<CollectSuccessPage />} />
      <Route path="/adjust" element={<AdjustPage />} />
      <Route path="/tutorial" element={<TutorialPage />} />
      <Route path="/eyes" element={<EyeGuidePage />} />
      <Route path="/library" element={<LibraryPage />} />
      <Route path="/mix" element={<MixPage />} />
      <Route path="/mix/generating" element={<MixGeneratingPage />} />
      <Route path="/mix/preview" element={<MixPreviewPage />} />
      <Route path="/profile" element={<ProfilePage />} />
    </Routes>
  );
}

export default function App() {
  return <AppRoutes />;
}
