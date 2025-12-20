const express = require('express');
const router = express.Router();
const multer = require('multer');
const axios = require('axios');
const FormData = require('form-data');
const Claim = require('../models/Claim');
const fs = require('fs');

// Configure multer for file uploads
const upload = multer({ dest: 'uploads/' });

// Submit new claim for analysis
router.post('/analyze', upload.single('image'), async (req, res) => {
  try {
    const { claim_date, claim_description, claim_location, policy_id } = req.body;
    
    if (!req.file) {
      return res.status(400).json({ error: 'Image file is required' });
    }
    
    if (!claim_date || !claim_description) {
      return res.status(400).json({ error: 'Claim date and description are required' });
    }
    
    // Forward to ML API
    const formData = new FormData();
    formData.append('image', fs.createReadStream(req.file.path), req.file.originalname);
    formData.append('claim_date', claim_date);
    formData.append('claim_description', claim_description);
    formData.append('claim_location', claim_location || 'Unknown');
    formData.append('policy_id', policy_id || '');
    
    let mlResponse;
    try {
      mlResponse = await axios.post(
        `${process.env.ML_API_URL}/api/analyze-claim`,
        formData,
        {
          headers: formData.getHeaders(),
          timeout: 180000 // 3 minutes
        }
      );
    } catch (mlError) {
      // Clean up uploaded file on ML API error
      if (req.file && fs.existsSync(req.file.path)) {
        fs.unlinkSync(req.file.path);
      }
      
      console.error('ML API Error:', mlError.message);
      return res.status(503).json({ 
        error: 'ML Backend is not available. Please ensure the ML service is running on port 8000.',
        details: mlError.code === 'ECONNREFUSED' ? 'Connection refused - ML backend not running' : mlError.message
      });
    }
    
    // Clean up uploaded file
    fs.unlinkSync(req.file.path);
    
    if (!mlResponse.data.success) {
      return res.status(500).json({ error: 'ML analysis failed' });
    }
    
    const result = mlResponse.data;
    
    // Save to MongoDB
    const claim = new Claim({
      jobId: result.job_id,
      claimInfo: {
        date: claim_date,
        description: claim_description,
        location: claim_location || 'Unknown',
        policyId: policy_id || ''
      },
      metadata: result.report?.damage_assessment?.metadata || {},
      analysis: {
        damageAssessment: {
          severity: result.report.damage_assessment.severity,
          damagedParts: result.report.damage_assessment.damaged_parts,
          description: result.report.damage_assessment.description,
          score: result.report.damage_assessment.score
        },
        fraudAnalysis: {
          overallScore: result.report.fraud_analysis.overall_score,
          riskLevel: result.report.fraud_analysis.risk_level,
          isDuplicate: result.report.fraud_analysis.is_duplicate,
          fraudIndicators: result.report.fraud_analysis.fraud_indicators,
          breakdown: result.report.fraud_analysis.breakdown
        },
        consistencyAnalysis: {
          score: result.report.consistency_analysis.score,
          isConsistent: result.report.consistency_analysis.is_consistent,
          explanation: result.report.consistency_analysis.explanation
        }
      },
      decision: {
        recommendation: result.report.decision.recommendation,
        confidence: result.report.decision.confidence,
        explanation: result.report.decision.explanation,
        scores: result.report.decision.scores
      },
      annotatedImagePath: result.annotated_image_url,
      status: 'PROCESSED'
    });
    
    await claim.save();
    
    res.json({
      success: true,
      claim: claim
    });
    
  } catch (error) {
    console.error('Error analyzing claim:', error);
    
    // Clean up file on error
    if (req.file && fs.existsSync(req.file.path)) {
      fs.unlinkSync(req.file.path);
    }
    
    res.status(500).json({
      error: 'Failed to analyze claim',
      details: error.message
    });
  }
});

// Get all claims with filtering
router.get('/', async (req, res) => {
  try {
    const { status, recommendation, policy_id, limit = 50, skip = 0 } = req.query;
    
    const filter = {};
    if (status) filter.status = status;
    if (recommendation) filter['decision.recommendation'] = recommendation;
    if (policy_id) filter['claimInfo.policyId'] = policy_id;
    
    const claims = await Claim.find(filter)
      .sort({ createdAt: -1 })
      .limit(parseInt(limit))
      .skip(parseInt(skip))
      .select('-__v');
    
    const total = await Claim.countDocuments(filter);
    
    res.json({
      success: true,
      total,
      claims
    });
    
  } catch (error) {
    console.error('Error fetching claims:', error);
    res.status(500).json({ error: 'Failed to fetch claims' });
  }
});

// Get single claim by ID
router.get('/:jobId', async (req, res) => {
  try {
    const claim = await Claim.findOne({ jobId: req.params.jobId });
    
    if (!claim) {
      return res.status(404).json({ error: 'Claim not found' });
    }
    
    res.json({
      success: true,
      claim
    });
    
  } catch (error) {
    console.error('Error fetching claim:', error);
    res.status(500).json({ error: 'Failed to fetch claim' });
  }
});

// Update claim status (for assessor review)
router.patch('/:jobId/status', async (req, res) => {
  try {
    const { status, assessorNotes } = req.body;
    
    const validStatuses = ['PENDING', 'PROCESSED', 'REVIEWED', 'APPROVED', 'REJECTED'];
    if (!validStatuses.includes(status)) {
      return res.status(400).json({ error: 'Invalid status' });
    }
    
    const claim = await Claim.findOne({ jobId: req.params.jobId });
    if (!claim) {
      return res.status(404).json({ error: 'Claim not found' });
    }
    
    claim.status = status;
    if (assessorNotes) {
      claim.assessorNotes = assessorNotes;
    }
    
    await claim.save();
    
    res.json({
      success: true,
      claim
    });
    
  } catch (error) {
    console.error('Error updating claim:', error);
    res.status(500).json({ error: 'Failed to update claim' });
  }
});

// Assessor override decision
router.patch('/:jobId/override', async (req, res) => {
  try {
    const { newRecommendation, reason, assessorId } = req.body;
    
    const validRecommendations = ['APPROVE', 'MANUAL_REVIEW', 'REJECT'];
    if (!validRecommendations.includes(newRecommendation)) {
      return res.status(400).json({ error: 'Invalid recommendation' });
    }
    
    const claim = await Claim.findOne({ jobId: req.params.jobId });
    if (!claim) {
      return res.status(404).json({ error: 'Claim not found' });
    }
    
    claim.assessorOverride = {
      applied: true,
      originalRecommendation: claim.decision.recommendation,
      newRecommendation,
      reason,
      assessorId,
      timestamp: new Date()
    };
    
    claim.decision.recommendation = newRecommendation;
    claim.status = newRecommendation === 'APPROVE' ? 'APPROVED' : 
                   newRecommendation === 'REJECT' ? 'REJECTED' : 'REVIEWED';
    
    await claim.save();
    
    res.json({
      success: true,
      claim
    });
    
  } catch (error) {
    console.error('Error overriding decision:', error);
    res.status(500).json({ error: 'Failed to override decision' });
  }
});

// Get statistics
router.get('/stats/summary', async (req, res) => {
  try {
    const totalClaims = await Claim.countDocuments();
    
    const statusCounts = await Claim.aggregate([
      { $group: { _id: '$status', count: { $sum: 1 } } }
    ]);
    
    const recommendationCounts = await Claim.aggregate([
      { $group: { _id: '$decision.recommendation', count: { $sum: 1 } } }
    ]);
    
    const avgScores = await Claim.aggregate([
      {
        $group: {
          _id: null,
          avgDamageScore: { $avg: '$decision.scores.damage' },
          avgFraudScore: { $avg: '$decision.scores.fraud' },
          avgConsistencyScore: { $avg: '$decision.scores.consistency' }
        }
      }
    ]);
    
    res.json({
      success: true,
      stats: {
        totalClaims,
        statusDistribution: statusCounts,
        recommendationDistribution: recommendationCounts,
        averageScores: avgScores[0] || {}
      }
    });
    
  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ error: 'Failed to fetch statistics' });
  }
});

module.exports = router;
