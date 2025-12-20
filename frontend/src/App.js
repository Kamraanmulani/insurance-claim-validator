import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import ClaimSubmission from './components/ClaimSubmission';
import ClaimsDashboard from './components/ClaimsDashboard';
import ClaimDetail from './components/ClaimDetail';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-bold text-gray-900">
                  Insurance Claim Validator
                </h1>
              </div>
              <div className="flex items-center space-x-4">
                <a href="/submit" className="text-gray-700 hover:text-blue-600">
                  Submit Claim
                </a>
                <a href="/dashboard" className="text-gray-700 hover:text-blue-600">
                  Dashboard
                </a>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" />} />
            <Route path="/submit" element={<ClaimSubmission onClaimSubmitted={(claim) => window.location.href = `/claim/${claim.jobId}`} />} />
            <Route path="/dashboard" element={<ClaimsDashboard />} />
            <Route path="/claim/:jobId" element={<ClaimDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
