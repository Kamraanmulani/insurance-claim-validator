import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { claimAPI } from '../services/api';

const ClaimDetail = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [claim, setClaim] = useState(null);
  const [loading, setLoading] = useState(true);
  const [overrideMode, setOverrideMode] = useState(false);
  const [overrideData, setOverrideData] = useState({
    newRecommendation: '',
    reason: ''
  });

  useEffect(() => {
    const loadClaim = async () => {
      try {
        setLoading(true);
        const response = await claimAPI.getClaim(jobId);
        setClaim(response.claim);
      } catch (error) {
        console.error('Error fetching claim:', error);
      } finally {
        setLoading(false);
      }
    };
    loadClaim();
  }, [jobId]);

  const handleOverride = async () => {
    try {
      await claimAPI.overrideDecision(
        jobId,
        overrideData.newRecommendation,
        overrideData.reason,
        'ASSESSOR-001' // In production, use actual assessor ID
      );
      setOverrideMode(false);
      // Reload the claim
      const response = await claimAPI.getClaim(jobId);
      setClaim(response.claim);
    } catch (error) {
      console.error('Error overriding decision:', error);
      alert('Failed to override decision');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!claim) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <p className="text-gray-500">Claim not found</p>
      </div>
    );
  }

  const ML_API_URL = process.env.REACT_APP_ML_API_URL || 'http://localhost:8000';

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center text-blue-600 hover:text-blue-700 mb-4"
        >
          <ArrowLeft size={20} className="mr-2" />
          Back to Dashboard
        </button>
        <h1 className="text-3xl font-bold text-gray-900">Claim Details</h1>
        <p className="text-gray-600">Job ID: {claim.jobId}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Annotated Image */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Damage Analysis</h2>
            <img
              src={`${ML_API_URL}${claim.annotatedImagePath}`}
              alt="Annotated damage"
              className="w-full rounded-lg"
              onError={(e) => {
                e.target.src = 'https://via.placeholder.com/800x600?text=Image+Not+Available';
              }}
            />
          </div>

          {/* AI Analysis */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">AI Analysis</h2>
            
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-700 mb-2">Damaged Parts</h3>
                <div className="flex flex-wrap gap-2">
                  {claim.analysis.damageAssessment.damagedParts.map((part, index) => (
                    <span key={index} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                      {part}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="font-semibold text-gray-700 mb-2">Damage Description</h3>
                <p className="text-gray-600">{claim.analysis.damageAssessment.description}</p>
              </div>

              <div>
                <h3 className="font-semibold text-gray-700 mb-2">Consistency Check</h3>
                <div className="space-y-3">
                  {/* Status Badge */}
                  <div className={`p-3 rounded-lg flex items-center justify-between ${
                    claim.analysis.consistencyAnalysis.score >= 8 ? 'bg-green-100' :
                    claim.analysis.consistencyAnalysis.score >= 5 ? 'bg-yellow-100' :
                    'bg-red-100'
                  }`}>
                    <div className="flex items-center gap-2">
                      {claim.analysis.consistencyAnalysis.score >= 8 ? (
                        <>
                          <CheckCircle2 size={20} className="text-green-600" />
                          <span className="font-semibold text-green-900">Story Matches Photo</span>
                        </>
                      ) : claim.analysis.consistencyAnalysis.score >= 5 ? (
                        <>
                          <AlertTriangle size={20} className="text-yellow-600" />
                          <span className="font-semibold text-yellow-900">Needs Review</span>
                        </>
                      ) : (
                        <>
                          <AlertTriangle size={20} className="text-red-600" />
                          <span className="font-semibold text-red-900">Mismatch Detected</span>
                        </>
                      )}
                    </div>
                    <span className={`text-lg font-bold ${
                      claim.analysis.consistencyAnalysis.score >= 8 ? 'text-green-700' :
                      claim.analysis.consistencyAnalysis.score >= 5 ? 'text-yellow-700' :
                      'text-red-700'
                    }`}>
                      {claim.analysis.consistencyAnalysis.score.toFixed(1)}/10
                    </span>
                  </div>

                  {/* Progress Bar */}
                  <div>
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>Match Accuracy</span>
                      <span>{claim.analysis.consistencyAnalysis.score >= 8 ? 'Excellent' : 
                             claim.analysis.consistencyAnalysis.score >= 5 ? 'Fair' : 'Poor'}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          claim.analysis.consistencyAnalysis.score >= 8 ? 'bg-green-600' :
                          claim.analysis.consistencyAnalysis.score >= 5 ? 'bg-yellow-600' :
                          'bg-red-600'
                        }`}
                        style={{ width: `${claim.analysis.consistencyAnalysis.score * 10}%` }}
                      />
                    </div>
                  </div>

                  {/* Explanation */}
                  {/* <p className="text-sm text-gray-600">{claim.analysis.consistencyAnalysis.explanation}</p> */}
                </div>
              </div>
            </div>
          </div>

          {/* Fraud Indicators */}
          {claim.analysis.fraudAnalysis.fraudIndicators.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <div className="flex items-start">
                <AlertTriangle className="text-red-500 mr-3 flex-shrink-0" size={24} />
                <div>
                  <h3 className="font-semibold text-red-900 mb-2">Fraud Indicators Detected</h3>
                  <ul className="list-disc list-inside space-y-1 text-red-700">
                    {claim.analysis.fraudAnalysis.fraudIndicators.map((indicator, index) => (
                      <li key={index}>{indicator}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Decision Card */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Decision</h2>
            
            <div className={`p-4 rounded-lg mb-4 ${
              claim.decision.recommendation === 'APPROVE' ? 'bg-green-100' :
              claim.decision.recommendation === 'REJECT' ? 'bg-red-100' :
              'bg-yellow-100'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-lg">
                  {claim.decision.recommendation.replace('_', ' ')}
                </span>
                {claim.decision.recommendation === 'APPROVE' && <CheckCircle2 className="text-green-600" />}
                {claim.decision.recommendation === 'REJECT' && <AlertTriangle className="text-red-600" />}
              </div>
              <p className="text-sm text-gray-700">
                Confidence: {claim.decision.confidence}
              </p>
            </div>

            <p className="text-sm text-gray-600 mb-4">
              {claim.decision.explanation}
            </p>

            {!overrideMode ? (
              <button
                onClick={() => setOverrideMode(true)}
                className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition"
              >
                Override Decision
              </button>
            ) : (
              <div className="space-y-3">
                <select
                  value={overrideData.newRecommendation}
                  onChange={(e) => setOverrideData({ ...overrideData, newRecommendation: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="">Select new decision</option>
                  <option value="APPROVE">Approve</option>
                  <option value="MANUAL_REVIEW">Manual Review</option>
                  <option value="REJECT">Reject</option>
                </select>

                <textarea
                  value={overrideData.reason}
                  onChange={(e) => setOverrideData({ ...overrideData, reason: e.target.value })}
                  placeholder="Reason for override..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />

                <div className="flex gap-2">
                  <button
                    onClick={handleOverride}
                    disabled={!overrideData.newRecommendation || !overrideData.reason}
                    className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                  >
                    Confirm
                  </button>
                  <button
                    onClick={() => setOverrideMode(false)}
                    className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Scores */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Scores</h2>
            
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium">Damage</span>
                  <span className="text-sm font-semibold">{claim.decision.scores.damage.toFixed(1)}/10</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${claim.decision.scores.damage * 10}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium">Fraud Risk</span>
                  <span className="text-sm font-semibold">{claim.decision.scores.fraud.toFixed(1)}/10</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-red-600 h-2 rounded-full"
                    style={{ width: `${claim.decision.scores.fraud * 10}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium">Consistency</span>
                  <span className="text-sm font-semibold">{claim.decision.scores.consistency.toFixed(1)}/10</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: `${claim.decision.scores.consistency * 10}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Claim Info */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Claim Information</h2>
            
            <div className="space-y-3 text-sm">
              <div>
                <span className="text-gray-500">Policy ID:</span>
                <span className="ml-2 font-medium">{claim.claimInfo.policyId || 'N/A'}</span>
              </div>
              <div>
                <span className="text-gray-500">Incident Date:</span>
                <span className="ml-2 font-medium">{new Date(claim.claimInfo.date).toLocaleDateString()}</span>
              </div>
              <div>
                <span className="text-gray-500">Location:</span>
                <span className="ml-2 font-medium">{claim.claimInfo.location}</span>
              </div>
              <div>
                <span className="text-gray-500">Severity:</span>
                <span className="ml-2 font-medium">{claim.analysis.damageAssessment.severity}</span>
              </div>
              <div>
                <span className="text-gray-500">Submitted:</span>
                <span className="ml-2 font-medium">{new Date(claim.createdAt).toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClaimDetail;
