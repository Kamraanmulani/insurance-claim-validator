const mongoose = require('mongoose');

const claimSchema = new mongoose.Schema({
  jobId: {
    type: String,
    required: true,
    unique: true
  },
  claimInfo: {
    date: { type: String, required: true },
    description: { type: String, required: true },
    location: { type: String },
    policyId: { type: String }
  },
  metadata: {
    has_exif: Boolean,
    timestamp: String,
    camera_make: String,
    camera_model: String,
    software: String,
    file_size_mb: Number
  },
  analysis: {
    damageAssessment: {
      severity: String,
      damagedParts: [String],
      description: String,
      score: Number
    },
    fraudAnalysis: {
      overallScore: Number,
      riskLevel: String,
      isDuplicate: Boolean,
      fraudIndicators: [String],
      breakdown: {
        metadataScore: Number,
        duplicateScore: Number,
        consistencyScore: Number
      }
    },
    consistencyAnalysis: {
      score: Number,
      isConsistent: Boolean,
      explanation: String
    }
  },
  decision: {
    recommendation: {
      type: String,
      enum: ['APPROVE', 'MANUAL_REVIEW', 'REJECT']
    },
    confidence: String,
    explanation: String,
    scores: {
      damage: Number,
      fraud: Number,
      consistency: Number
    }
  },
  annotatedImagePath: String,
  status: {
    type: String,
    enum: ['PENDING', 'PROCESSED', 'REVIEWED', 'APPROVED', 'REJECTED'],
    default: 'PROCESSED'
  },
  assessorNotes: String,
  assessorOverride: {
    applied: { type: Boolean, default: false },
    originalRecommendation: String,
    newRecommendation: String,
    reason: String,
    assessorId: String,
    timestamp: Date
  }
}, {
  timestamps: true
});

// Index for faster queries
claimSchema.index({ 'claimInfo.policyId': 1 });
claimSchema.index({ 'decision.recommendation': 1 });
claimSchema.index({ status: 1 });

module.exports = mongoose.model('Claim', claimSchema);
