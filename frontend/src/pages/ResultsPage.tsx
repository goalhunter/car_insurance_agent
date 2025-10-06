import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Shield, CheckCircle, AlertTriangle, XCircle, FileText, DollarSign, TrendingUp, Download } from 'lucide-react';
import { getClaimStatus } from '../services/api';
import type { SettlementDecision, Customer, Policy, DamageAnalysis, DocumentAnalysis } from '../types';

export default function ResultsPage() {
  const { claimId } = useParams<{ claimId: string }>();
  const [loading, setLoading] = useState(true);
  const [claimData, setClaimData] = useState<{
    customer?: Customer;
    policy?: Policy;
    damageAnalysis?: DamageAnalysis;
    documentAnalysis?: DocumentAnalysis;
    settlement?: SettlementDecision;
  }>({});

  useEffect(() => {
    if (!claimId) return;

    getClaimStatus(claimId)
      .then((data) => {
        setClaimData(data);
        setLoading(false);
      })
      .catch(() => {
        // Mock data for demo when backend is not available
        const mockData = {
          customer: {
            customer_id: 'CUST-001',
            first_name: 'John',
            last_name: 'Doe',
            email: 'john.doe@example.com',
            phone: '+1-555-0123',
            age: 35,
            driving_experience_years: 15,
            previous_claims_count: 1,
          },
          policy: {
            policy_id: 'POL-001',
            policy_number: 'POL-12345',
            policy_type: 'Comprehensive',
            policy_status: 'Active',
            coverage_amount: 50000,
            deductible_amount: 1000,
            premium_amount: 1200,
            customer_id: 'CUST-001',
            policy_start_date: '2024-01-01',
            policy_end_date: '2025-01-01',
          },
          damageAnalysis: {
            vehicle_match: true,
            analysis: {
              vehicle_matches_policy: true,
              damaged_parts: ['Front Bumper', 'Hood', 'Left Headlight'],
              damage_summary: 'Moderate front-end collision damage',
              estimated_repair_cost_usd: 4500,
              likely_crash_reason: 'Rear-end collision',
              severity: 'moderate' as const,
              suspicious_indicators: [],
            },
          },
          documentAnalysis: {
            incident_date: '2025-10-01',
            incident_location: 'Highway 101, San Francisco, CA',
            police_case_number: 'PC-2025-10-001',
            fault_determination: 'Not at fault',
            estimated_repair_cost: 4500,
            repair_items: ['Replace front bumper', 'Repair hood', 'Replace left headlight'],
            inconsistencies: [],
            red_flags: [],
          },
          settlement: {
            claim_id: claimId,
            recommendation: 'APPROVE' as const,
            approved_amount: 4500,
            deductible_applies: true,
            customer_pays: 1000,
            insurance_pays: 3500,
            genuine_factors: [
              'Clean driving record',
              'Consistent documentation',
              'Police report matches damage',
              'No previous fraud indicators',
            ],
            suspicious_factors: [],
            risk_assessment: 'low' as const,
            detailed_reasoning: 'All documentation is consistent. Customer has a clean record. Damage matches the reported incident. Police report confirms the customer was not at fault.',
            supporting_evidence: [
              'Police report PC-2025-10-001',
              'Repair estimate from certified shop',
              'Damage photos match incident description',
            ],
            next_steps: [
              'Payment of $3,500 will be processed within 3-5 business days',
              'Customer responsible for $1,000 deductible',
              'Approved repair shop list has been sent to customer email',
              'Claims adjuster will contact within 24 hours',
            ],
          },
        };
        setClaimData(mockData);
        setLoading(false);
      });
  }, [claimId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Shield className="h-16 w-16 text-blue-600 mx-auto animate-pulse mb-4" />
          <p className="text-gray-600">Loading claim results...</p>
        </div>
      </div>
    );
  }

  const { settlement, customer, policy, damageAnalysis, documentAnalysis } = claimData;

  const getRecommendationColor = (recommendation?: string) => {
    switch (recommendation) {
      case 'APPROVE':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'MANUAL_REVIEW':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'DENY':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getRecommendationIcon = (recommendation?: string) => {
    switch (recommendation) {
      case 'APPROVE':
        return <CheckCircle className="h-8 w-8" />;
      case 'MANUAL_REVIEW':
        return <AlertTriangle className="h-8 w-8" />;
      case 'DENY':
        return <XCircle className="h-8 w-8" />;
      default:
        return <FileText className="h-8 w-8" />;
    }
  };

  const getRiskColor = (risk?: string) => {
    switch (risk) {
      case 'low':
        return 'text-green-600';
      case 'medium':
        return 'text-yellow-600';
      case 'high':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <Shield className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">Claim Results</h1>
            </div>
            <Link
              to="/"
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Return to Home
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Settlement Decision */}
        {settlement && (
          <div
            className={`mb-8 rounded-lg border-2 p-6 ${getRecommendationColor(
              settlement.recommendation
            )}`}
          >
            <div className="flex items-center space-x-4 mb-4">
              {getRecommendationIcon(settlement.recommendation)}
              <div>
                <h2 className="text-2xl font-bold">
                  Claim {settlement.recommendation === 'APPROVE' ? 'Approved' : settlement.recommendation === 'DENY' ? 'Denied' : 'Under Review'}
                </h2>
                <p className="text-sm opacity-90">Claim ID: {settlement.claim_id}</p>
              </div>
            </div>

            {settlement.recommendation === 'APPROVE' && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                <div className="bg-white rounded-lg p-4">
                  <p className="text-sm text-gray-600">Approved Amount</p>
                  <p className="text-2xl font-bold text-green-600">
                    ${settlement.approved_amount.toLocaleString()}
                  </p>
                </div>
                <div className="bg-white rounded-lg p-4">
                  <p className="text-sm text-gray-600">You Pay (Deductible)</p>
                  <p className="text-2xl font-bold text-gray-900">
                    ${settlement.customer_pays.toLocaleString()}
                  </p>
                </div>
                <div className="bg-white rounded-lg p-4">
                  <p className="text-sm text-gray-600">Insurance Pays</p>
                  <p className="text-2xl font-bold text-blue-600">
                    ${settlement.insurance_pays.toLocaleString()}
                  </p>
                </div>
              </div>
            )}

            <div className="mt-6 bg-white rounded-lg p-4">
              <h3 className="font-semibold mb-2">Decision Reasoning</h3>
              <p className="text-sm">{settlement.detailed_reasoning}</p>
            </div>

            {settlement.pdf_url && (
              <div className="mt-4">
                <a
                  href={settlement.pdf_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-3 rounded-lg transition-colors"
                >
                  <Download className="h-5 w-5" />
                  <span>Download Settlement Decision (PDF)</span>
                </a>
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Risk Assessment */}
          {settlement && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center space-x-2 mb-4">
                <TrendingUp className="h-6 w-6 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">Risk Assessment</h3>
              </div>

              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-1">Risk Level</p>
                <p className={`text-2xl font-bold ${getRiskColor(settlement.risk_assessment)}`}>
                  {settlement.risk_assessment?.toUpperCase()}
                </p>
              </div>

              {settlement.genuine_factors && settlement.genuine_factors.length > 0 && (
                <div className="mb-4">
                  <p className="text-sm font-semibold text-green-600 mb-2">✓ Genuine Factors</p>
                  <ul className="space-y-1">
                    {settlement.genuine_factors.map((factor, idx) => (
                      <li key={idx} className="text-sm text-gray-700">
                        • {factor}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {settlement.suspicious_factors && settlement.suspicious_factors.length > 0 && (
                <div>
                  <p className="text-sm font-semibold text-red-600 mb-2">⚠ Suspicious Factors</p>
                  <ul className="space-y-1">
                    {settlement.suspicious_factors.map((factor, idx) => (
                      <li key={idx} className="text-sm text-gray-700">
                        • {factor}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Customer & Policy Info */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center space-x-2 mb-4">
              <FileText className="h-6 w-6 text-blue-600" />
              <h3 className="text-lg font-semibold text-gray-900">Customer & Policy</h3>
            </div>

            {customer && (
              <div className="mb-4 pb-4 border-b">
                <p className="text-sm text-gray-600 mb-2">Customer Information</p>
                <p className="text-sm">
                  <strong>Name:</strong> {customer.first_name} {customer.last_name}
                </p>
                <p className="text-sm">
                  <strong>Email:</strong> {customer.email}
                </p>
                {customer.phone && (
                  <p className="text-sm">
                    <strong>Phone:</strong> {customer.phone}
                  </p>
                )}
                {customer.previous_claims_count !== undefined && (
                  <p className="text-sm">
                    <strong>Previous Claims:</strong> {customer.previous_claims_count}
                  </p>
                )}
              </div>
            )}

            {policy && (
              <div>
                <p className="text-sm text-gray-600 mb-2">Policy Information</p>
                <p className="text-sm">
                  <strong>Policy Number:</strong> {policy.policy_number}
                </p>
                <p className="text-sm">
                  <strong>Type:</strong> {policy.policy_type}
                </p>
                <p className="text-sm">
                  <strong>Status:</strong> {policy.policy_status}
                </p>
                <p className="text-sm">
                  <strong>Coverage:</strong> ${policy.coverage_amount.toLocaleString()}
                </p>
                <p className="text-sm">
                  <strong>Deductible:</strong> ${policy.deductible_amount.toLocaleString()}
                </p>
              </div>
            )}
          </div>

          {/* Damage Analysis */}
          {damageAnalysis && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center space-x-2 mb-4">
                <AlertTriangle className="h-6 w-6 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">Damage Analysis</h3>
              </div>

              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-600">Severity</p>
                  <p className={`text-lg font-semibold ${
                    damageAnalysis.analysis.severity === 'severe' ? 'text-red-600' :
                    damageAnalysis.analysis.severity === 'moderate' ? 'text-yellow-600' :
                    'text-green-600'
                  }`}>
                    {damageAnalysis.analysis.severity?.toUpperCase()}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-gray-600">Estimated Repair Cost</p>
                  <p className="text-lg font-semibold text-gray-900">
                    ${damageAnalysis.analysis.estimated_repair_cost_usd.toLocaleString()}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-gray-600 mb-1">Damaged Parts</p>
                  <div className="flex flex-wrap gap-2">
                    {damageAnalysis.analysis.damaged_parts.map((part, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full"
                      >
                        {part}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-600">Damage Summary</p>
                  <p className="text-sm text-gray-700">{damageAnalysis.analysis.damage_summary}</p>
                </div>

                <div>
                  <p className="text-sm text-gray-600">Likely Cause</p>
                  <p className="text-sm text-gray-700">{damageAnalysis.analysis.likely_crash_reason}</p>
                </div>
              </div>
            </div>
          )}

          {/* Document Analysis */}
          {documentAnalysis && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center space-x-2 mb-4">
                <FileText className="h-6 w-6 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">Document Analysis</h3>
              </div>

              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-600">Incident Date</p>
                  <p className="text-sm text-gray-900">{documentAnalysis.incident_date}</p>
                </div>

                <div>
                  <p className="text-sm text-gray-600">Location</p>
                  <p className="text-sm text-gray-900">{documentAnalysis.incident_location}</p>
                </div>

                {documentAnalysis.police_case_number && (
                  <div>
                    <p className="text-sm text-gray-600">Police Case Number</p>
                    <p className="text-sm text-gray-900">{documentAnalysis.police_case_number}</p>
                  </div>
                )}

                <div>
                  <p className="text-sm text-gray-600">Fault Determination</p>
                  <p className="text-sm text-gray-900">{documentAnalysis.fault_determination}</p>
                </div>

                {documentAnalysis.repair_items && documentAnalysis.repair_items.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Repair Items</p>
                    <ul className="space-y-1">
                      {documentAnalysis.repair_items.map((item, idx) => (
                        <li key={idx} className="text-sm text-gray-700">
                          • {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {documentAnalysis.red_flags && documentAnalysis.red_flags.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-red-600 mb-1">Red Flags</p>
                    <ul className="space-y-1">
                      {documentAnalysis.red_flags.map((flag, idx) => (
                        <li key={idx} className="text-sm text-gray-700">
                          ⚠ {flag}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Next Steps */}
        {settlement && settlement.next_steps && settlement.next_steps.length > 0 && (
          <div className="mt-8 bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center space-x-2 mb-4">
              <DollarSign className="h-6 w-6 text-blue-600" />
              <h3 className="text-lg font-semibold text-gray-900">Next Steps</h3>
            </div>
            <ul className="space-y-2">
              {settlement.next_steps.map((step, idx) => (
                <li key={idx} className="flex items-start space-x-2">
                  <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                    {idx + 1}
                  </span>
                  <p className="text-sm text-gray-700 pt-0.5">{step}</p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
