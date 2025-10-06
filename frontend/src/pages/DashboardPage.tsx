import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Shield, TrendingUp, Clock, CheckCircle, AlertTriangle, XCircle, Search } from 'lucide-react';
import { listClaims } from '../services/api';

interface ClaimSummary {
  claim_id: string;
  customer_name: string;
  policy_number: string;
  status: 'APPROVE' | 'MANUAL_REVIEW' | 'DENY' | 'IN_PROGRESS';
  risk_level?: 'low' | 'medium' | 'high';
  amount?: number;
  created_at: string;
}

export default function DashboardPage() {
  const [claims, setClaims] = useState<ClaimSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');

  useEffect(() => {
    listClaims()
      .then((data) => {
        setClaims(data);
        setLoading(false);
      })
      .catch(() => {
        // Mock data for demo when backend is not available
        const mockClaims: ClaimSummary[] = [
          {
            claim_id: 'CLM-2025-001-ABC123',
            customer_name: 'John Doe',
            policy_number: 'POL-12345',
            status: 'APPROVE',
            risk_level: 'low',
            amount: 4500,
            created_at: new Date().toISOString(),
          },
          {
            claim_id: 'CLM-2025-002-DEF456',
            customer_name: 'Jane Smith',
            policy_number: 'POL-67890',
            status: 'MANUAL_REVIEW',
            risk_level: 'medium',
            amount: 8200,
            created_at: new Date(Date.now() - 86400000).toISOString(),
          },
          {
            claim_id: 'CLM-2025-003-GHI789',
            customer_name: 'Bob Johnson',
            policy_number: 'POL-11223',
            status: 'DENY',
            risk_level: 'high',
            amount: 12000,
            created_at: new Date(Date.now() - 172800000).toISOString(),
          },
        ];
        setClaims(mockClaims);
        setLoading(false);
      });
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'APPROVE':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'MANUAL_REVIEW':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case 'DENY':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'IN_PROGRESS':
        return <Clock className="h-5 w-5 text-blue-600" />;
      default:
        return <Clock className="h-5 w-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'APPROVE':
        return 'bg-green-50 text-green-700 border-green-200';
      case 'MANUAL_REVIEW':
        return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      case 'DENY':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'IN_PROGRESS':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  const getRiskBadge = (risk?: string) => {
    if (!risk) return null;

    const colors = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-red-100 text-red-800',
    };

    return (
      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${colors[risk as keyof typeof colors]}`}>
        {risk.toUpperCase()} RISK
      </span>
    );
  };

  const filteredClaims = claims.filter((claim) => {
    const matchesSearch =
      claim.claim_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      claim.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      claim.policy_number.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFilter = filterStatus === 'ALL' || claim.status === filterStatus;

    return matchesSearch && matchesFilter;
  });

  const stats = {
    total: claims.length,
    approved: claims.filter((c) => c.status === 'APPROVE').length,
    pending: claims.filter((c) => c.status === 'MANUAL_REVIEW').length,
    denied: claims.filter((c) => c.status === 'DENY').length,
    inProgress: claims.filter((c) => c.status === 'IN_PROGRESS').length,
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Shield className="h-16 w-16 text-blue-600 mx-auto animate-pulse mb-4" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <Shield className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">Claims Dashboard</h1>
            </div>
            <nav className="flex space-x-6">
              <Link to="/" className="text-gray-700 hover:text-blue-600">
                Home
              </Link>
              <Link to="/claim" className="text-blue-600 hover:text-blue-700 font-medium">
                File New Claim
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <StatCard
            icon={<TrendingUp className="h-6 w-6" />}
            label="Total Claims"
            value={stats.total}
            color="blue"
          />
          <StatCard
            icon={<CheckCircle className="h-6 w-6" />}
            label="Approved"
            value={stats.approved}
            color="green"
          />
          <StatCard
            icon={<AlertTriangle className="h-6 w-6" />}
            label="Under Review"
            value={stats.pending}
            color="yellow"
          />
          <StatCard
            icon={<XCircle className="h-6 w-6" />}
            label="Denied"
            value={stats.denied}
            color="red"
          />
          <StatCard
            icon={<Clock className="h-6 w-6" />}
            label="In Progress"
            value={stats.inProgress}
            color="blue"
          />
        </div>

        {/* Filters and Search */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0 md:space-x-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search by claim ID, customer name, or policy number..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Filter */}
            <div className="flex space-x-2">
              {['ALL', 'APPROVE', 'MANUAL_REVIEW', 'DENY', 'IN_PROGRESS'].map((status) => (
                <button
                  key={status}
                  onClick={() => setFilterStatus(status)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filterStatus === status
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {status === 'MANUAL_REVIEW' ? 'Review' : status === 'IN_PROGRESS' ? 'Progress' : status}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Claims Table */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Claim ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Customer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Policy Number
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredClaims.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                      {searchTerm || filterStatus !== 'ALL'
                        ? 'No claims match your filters'
                        : 'No claims found'}
                    </td>
                  </tr>
                ) : (
                  filteredClaims.map((claim) => (
                    <tr key={claim.claim_id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {claim.claim_id.substring(0, 8)}...
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {claim.customer_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {claim.policy_number}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(claim.status)}
                          <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${getStatusColor(claim.status)}`}>
                            {claim.status === 'MANUAL_REVIEW' ? 'REVIEW' : claim.status.replace('_', ' ')}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {getRiskBadge(claim.risk_level)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {claim.amount ? `$${claim.amount.toLocaleString()}` : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {new Date(claim.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <Link
                          to={`/results/${claim.claim_id}`}
                          className="text-blue-600 hover:text-blue-700 font-medium"
                        >
                          View Details
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Summary Footer */}
        {filteredClaims.length > 0 && (
          <div className="mt-4 text-sm text-gray-600 text-center">
            Showing {filteredClaims.length} of {claims.length} claims
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: 'blue' | 'green' | 'yellow' | 'red';
}) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    red: 'bg-red-50 text-red-600',
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className={`inline-flex items-center justify-center p-3 rounded-lg ${colorClasses[color]} mb-4`}>
        {icon}
      </div>
      <p className="text-sm text-gray-600 mb-1">{label}</p>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
    </div>
  );
}
