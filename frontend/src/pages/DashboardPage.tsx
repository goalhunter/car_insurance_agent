import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Box,
  Container,
  Heading,
  Text,
  Button,
  Input,
  Flex,
  Card,
  Badge,
  Spinner,
  SimpleGrid,
  Table,
} from '@chakra-ui/react';
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
        return '✅';
      case 'MANUAL_REVIEW':
        return '⚠️';
      case 'DENY':
        return '❌';
      case 'IN_PROGRESS':
        return '⏳';
      default:
        return '⏳';
    }
  };

  const getStatusColor = (status: string): 'green' | 'yellow' | 'red' | 'blue' | 'gray' => {
    switch (status) {
      case 'APPROVE':
        return 'green';
      case 'MANUAL_REVIEW':
        return 'yellow';
      case 'DENY':
        return 'red';
      case 'IN_PROGRESS':
        return 'blue';
      default:
        return 'gray';
    }
  };

  const getRiskColor = (risk?: string): 'green' | 'yellow' | 'red' | undefined => {
    if (!risk) return undefined;
    const colors = {
      low: 'green' as const,
      medium: 'yellow' as const,
      high: 'red' as const,
    };
    return colors[risk as keyof typeof colors];
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
      <Box minH="100vh" bg="gray.50" display="flex" alignItems="center" justifyContent="center">
        <Flex direction="column" align="center" gap={4}>
          <Spinner size="xl" color="blue.600" />
          <Text color="gray.600">Loading dashboard...</Text>
        </Flex>
      </Box>
    );
  }

  return (
    <Box minH="100vh" bg="gray.50">
      {/* Header */}
      <Box bg="white" boxShadow="sm" py={4}>
        <Container maxW="7xl">
          <Flex justify="space-between" align="center">
            <Flex align="center" gap={3}>
              <Text fontSize="2xl">🚗</Text>
              <Heading size="xl" color="gray.900">Claims Dashboard</Heading>
            </Flex>
            <Flex gap={6}>
              <Link to="/">
                <Text color="gray.700" _hover={{ color: 'blue.600' }}>Home</Text>
              </Link>
              <Link to="/claim">
                <Button colorPalette="blue" size="sm">File New Claim</Button>
              </Link>
            </Flex>
          </Flex>
        </Container>
      </Box>

      <Container maxW="7xl" py={8}>
        {/* Statistics */}
        <SimpleGrid columns={{ base: 1, md: 2, lg: 5 }} gap={6} mb={8}>
          <StatCard
            icon="📊"
            label="Total Claims"
            value={stats.total}
            color="blue"
          />
          <StatCard
            icon="✅"
            label="Approved"
            value={stats.approved}
            color="green"
          />
          <StatCard
            icon="⚠️"
            label="Under Review"
            value={stats.pending}
            color="yellow"
          />
          <StatCard
            icon="❌"
            label="Denied"
            value={stats.denied}
            color="red"
          />
          <StatCard
            icon="⏳"
            label="In Progress"
            value={stats.inProgress}
            color="blue"
          />
        </SimpleGrid>

        {/* Filters and Search */}
        <Card.Root bg="white" p={6} mb={6}>
          <Flex direction={{ base: 'column', md: 'row' }} gap={4} align={{ base: 'stretch', md: 'center' }} justify="space-between">
            {/* Search */}
            <Box flex="1">
              <Input
                type="text"
                placeholder="🔍 Search by claim ID, customer name, or policy number..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                size="md"
              />
            </Box>

            {/* Filter */}
            <Flex gap={2} flexWrap="wrap">
              {['ALL', 'APPROVE', 'MANUAL_REVIEW', 'DENY', 'IN_PROGRESS'].map((status) => (
                <Button
                  key={status}
                  onClick={() => setFilterStatus(status)}
                  size="sm"
                  variant={filterStatus === status ? 'solid' : 'outline'}
                  colorPalette={filterStatus === status ? 'blue' : 'gray'}
                >
                  {status === 'MANUAL_REVIEW' ? 'Review' : status === 'IN_PROGRESS' ? 'Progress' : status}
                </Button>
              ))}
            </Flex>
          </Flex>
        </Card.Root>

        {/* Claims Table */}
        <Card.Root bg="white" overflow="hidden">
          <Box overflowX="auto">
            <Table.Root size="md">
              <Table.Header>
                <Table.Row bg="gray.50">
                  <Table.ColumnHeader>Claim ID</Table.ColumnHeader>
                  <Table.ColumnHeader>Customer</Table.ColumnHeader>
                  <Table.ColumnHeader>Policy Number</Table.ColumnHeader>
                  <Table.ColumnHeader>Status</Table.ColumnHeader>
                  <Table.ColumnHeader>Risk</Table.ColumnHeader>
                  <Table.ColumnHeader>Amount</Table.ColumnHeader>
                  <Table.ColumnHeader>Created</Table.ColumnHeader>
                  <Table.ColumnHeader>Actions</Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {filteredClaims.length === 0 ? (
                  <Table.Row>
                    <Table.Cell colSpan={8} textAlign="center" py={12} color="gray.500">
                      {searchTerm || filterStatus !== 'ALL'
                        ? 'No claims match your filters'
                        : 'No claims found'}
                    </Table.Cell>
                  </Table.Row>
                ) : (
                  filteredClaims.map((claim) => (
                    <Table.Row key={claim.claim_id} _hover={{ bg: 'gray.50' }}>
                      <Table.Cell fontWeight="medium" fontSize="sm">
                        {claim.claim_id.substring(0, 8)}...
                      </Table.Cell>
                      <Table.Cell fontSize="sm">{claim.customer_name}</Table.Cell>
                      <Table.Cell fontSize="sm">{claim.policy_number}</Table.Cell>
                      <Table.Cell>
                        <Flex align="center" gap={2}>
                          <Text fontSize="lg">{getStatusIcon(claim.status)}</Text>
                          <Badge colorPalette={getStatusColor(claim.status)} size="sm">
                            {claim.status === 'MANUAL_REVIEW' ? 'REVIEW' : claim.status.replace('_', ' ')}
                          </Badge>
                        </Flex>
                      </Table.Cell>
                      <Table.Cell>
                        {claim.risk_level && (
                          <Badge colorPalette={getRiskColor(claim.risk_level)} size="sm">
                            {claim.risk_level.toUpperCase()} RISK
                          </Badge>
                        )}
                      </Table.Cell>
                      <Table.Cell fontSize="sm">
                        {claim.amount ? `$${claim.amount.toLocaleString()}` : '-'}
                      </Table.Cell>
                      <Table.Cell fontSize="sm">
                        {new Date(claim.created_at).toLocaleDateString()}
                      </Table.Cell>
                      <Table.Cell>
                        <Link to={`/results/${claim.claim_id}`}>
                          <Button variant="ghost" colorPalette="blue" size="sm">
                            View Details
                          </Button>
                        </Link>
                      </Table.Cell>
                    </Table.Row>
                  ))
                )}
              </Table.Body>
            </Table.Root>
          </Box>
        </Card.Root>

        {/* Summary Footer */}
        {filteredClaims.length > 0 && (
          <Text mt={4} fontSize="sm" color="gray.600" textAlign="center">
            Showing {filteredClaims.length} of {claims.length} claims
          </Text>
        )}
      </Container>
    </Box>
  );
}

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: string;
  label: string;
  value: number;
  color: 'blue' | 'green' | 'yellow' | 'red';
}) {
  return (
    <Card.Root bg="white" p={6}>
      <Flex direction="column" align="start">
        <Box
          bg={`${color}.50`}
          color={`${color}.600`}
          p={3}
          borderRadius="lg"
          mb={4}
          fontSize="2xl"
        >
          {icon}
        </Box>
        <Text fontSize="sm" color="gray.600" mb={1}>{label}</Text>
        <Text fontSize="3xl" fontWeight="bold" color="gray.900">{value}</Text>
      </Flex>
    </Card.Root>
  );
}
