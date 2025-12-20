import React, { useState } from 'react';
import { Upload, AlertCircle, CheckCircle, Loader } from 'lucide-react';
import { claimAPI } from '../services/api';

const ClaimSubmission = ({ onClaimSubmitted }) => {
  const [formData, setFormData] = useState({
    claim_date: '',
    claim_description: '',
    claim_location: '',
    policy_id: ''
  });
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const submitData = new FormData();
      submitData.append('image', image);
      submitData.append('claim_date', formData.claim_date);
      submitData.append('claim_description', formData.claim_description);
      submitData.append('claim_location', formData.claim_location);
      submitData.append('policy_id', formData.policy_id);

      const response = await claimAPI.submitClaim(submitData);

      setSuccess('Claim analyzed successfully!');
      setFormData({
        claim_date: '',
        claim_description: '',
        claim_location: '',
        policy_id: ''
      });
      setImage(null);
      setImagePreview(null);

      if (onClaimSubmitted) {
        onClaimSubmitted(response.claim);
      }

    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit claim');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto bg-white rounded-lg shadow-md p-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Submit New Claim</h2>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
          <AlertCircle className="text-red-500 mr-2 flex-shrink-0" size={20} />
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start">
          <CheckCircle className="text-green-500 mr-2 flex-shrink-0" size={20} />
          <p className="text-green-700">{success}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Image Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Damage Photo *
          </label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition">
            <input
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              className="hidden"
              id="image-upload"
              required
            />
            <label htmlFor="image-upload" className="cursor-pointer">
              {imagePreview ? (
                <img 
                  src={imagePreview} 
                  alt="Preview" 
                  className="max-h-64 mx-auto rounded-lg"
                />
              ) : (
                <div>
                  <Upload className="mx-auto text-gray-400 mb-2" size={48} />
                  <p className="text-gray-600">Click to upload damage photo</p>
                  <p className="text-sm text-gray-400 mt-1">PNG, JPG up to 10MB</p>
                </div>
              )}
            </label>
          </div>
        </div>

        {/* Policy ID */}
        <div>
          <label htmlFor="policy_id" className="block text-sm font-medium text-gray-700 mb-2">
            Policy ID
          </label>
          <input
            type="text"
            id="policy_id"
            name="policy_id"
            value={formData.policy_id}
            onChange={handleInputChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="POL-2025-001"
          />
        </div>

        {/* Claim Date */}
        <div>
          <label htmlFor="claim_date" className="block text-sm font-medium text-gray-700 mb-2">
            Incident Date *
          </label>
          <input
            type="date"
            id="claim_date"
            name="claim_date"
            value={formData.claim_date}
            onChange={handleInputChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          />
        </div>

        {/* Location */}
        <div>
          <label htmlFor="claim_location" className="block text-sm font-medium text-gray-700 mb-2">
            Location
          </label>
          <input
            type="text"
            id="claim_location"
            name="claim_location"
            value={formData.claim_location}
            onChange={handleInputChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="City, State"
          />
        </div>

        {/* Description */}
        <div>
          <label htmlFor="claim_description" className="block text-sm font-medium text-gray-700 mb-2">
            Incident Description *
          </label>
          <textarea
            id="claim_description"
            name="claim_description"
            value={formData.claim_description}
            onChange={handleInputChange}
            rows={4}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Describe the incident and damage in detail..."
            required
          />
          <p className="text-sm text-gray-500 mt-1">
            Be specific about what happened and what parts are damaged
          </p>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading || !image}
          className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center transition"
        >
          {loading ? (
            <>
              <Loader className="animate-spin mr-2" size={20} />
              Analyzing Claim... (This may take 1-2 minutes)
            </>
          ) : (
            'Submit Claim for Analysis'
          )}
        </button>
      </form>
    </div>
  );
};

export default ClaimSubmission;
