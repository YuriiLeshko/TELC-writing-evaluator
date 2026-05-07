import { useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import HomePage from "./pages/HomePage.jsx";
import TrainingPage from "./pages/TrainingPage.jsx";
import ResultPage from "./pages/ResultPage.jsx";
import ArchivePage from "./pages/ArchivePage.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import AdminPage from "./pages/AdminPage.jsx";
import AssessmentGuide from "./pages/AssessmentGuide.jsx";

const DISCLAIMER_KEY = "telc_disclaimer_accepted";

function RequireDisclaimer({ accepted, children }) {
  if (accepted) {
    return children;
  }
  return (
    <Navigate
      to="/"
      replace
      state={{ disclaimerRequired: true }}
    />
  );
}

export default function App() {
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(() => {
    try {
      return localStorage.getItem(DISCLAIMER_KEY) === "true";
    } catch {
      return false;
    }
  });

  const acceptDisclaimer = () => {
    try {
      localStorage.setItem(DISCLAIMER_KEY, "true");
    } catch {
      // ignore storage failures
    }
    setDisclaimerAccepted(true);
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route
          element={(
            <Layout
              disclaimerAccepted={disclaimerAccepted}
              onAcceptDisclaimer={acceptDisclaimer}
            />
          )}
        >
          <Route path="/" element={<HomePage />} />
          <Route
            path="/training"
            element={(
              <RequireDisclaimer accepted={disclaimerAccepted}>
                <TrainingPage />
              </RequireDisclaimer>
            )}
          />
          <Route path="/result" element={<ResultPage />} />
          <Route path="/assessment-guide" element={<AssessmentGuide />} />
          <Route
            path="/archive"
            element={(
              <RequireDisclaimer accepted={disclaimerAccepted}>
                <ArchivePage />
              </RequireDisclaimer>
            )}
          />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
