import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import PlanVisit from './pages/PlanVisit'
import VisitGuide from './pages/VisitGuide'
import CrowdControl from './pages/CrowdControl'
import MemoryPage from './pages/MemoryPage'
import EvaluationPage from './pages/EvaluationPage'
import About from './pages/About'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-museum-bg">
        <Navbar />
        <main className="pb-16">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/plan" element={<PlanVisit />} />
            <Route path="/guide/:visitId" element={<VisitGuide />} />
            <Route path="/crowd" element={<CrowdControl />} />
            <Route path="/memory" element={<MemoryPage />} />
            <Route path="/evaluation" element={<EvaluationPage />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
