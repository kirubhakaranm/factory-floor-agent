import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/layout/Layout";
import DashboardPage from "./pages/DashboardPage";
import ChatPage from "./pages/ChatPage";
import StationPage from "./pages/StationPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import VinTrackerPage from "./pages/VinTrackerPage";

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/station" element={<StationPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/vin" element={<VinTrackerPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
