import { Link } from 'react-router-dom';
import { Box, Container, Heading, Text, Button, SimpleGrid, Stack, Flex } from '@chakra-ui/react';

export default function LandingPage() {
  return (
    <Box>
      {/* Header */}
      <Box bg="white" boxShadow="sm" py={4}>
        <Container maxW="7xl">
          <Flex justify="space-between" align="center">
            <Flex align="center" gap={3}>
              <Text fontSize="2xl">🛡️</Text>
              <Heading size="xl" color="blue.600">AutoSettled</Heading>
            </Flex>
            <Flex gap={8}>
              <Link to="/"><Text color="gray.700" _hover={{ color: "blue.600" }}>Home</Text></Link>
              <Link to="/dashboard"><Text color="gray.700" _hover={{ color: "blue.600" }}>Dashboard</Text></Link>
            </Flex>
          </Flex>
        </Container>
      </Box>

      {/* Hero Section */}
      <Box bg="gradient-to-br(from-blue.50, to-indigo.100)" py={20}>
        <Container maxW="7xl">
          <Stack align="center" textAlign="center" gap={6}>
            <Heading size="4xl" color="gray.900">
              AI-Powered Car Insurance Claims
            </Heading>
            <Text fontSize="xl" color="gray.600" maxW="3xl">
              File your claim in minutes with our intelligent AI agent.
              Get instant damage assessment, fraud detection, and settlement decisions.
            </Text>
            <Link to="/claim">
              <Button size="xl" colorPalette="blue" px={8} py={6} fontSize="lg" boxShadow="lg">
                File a Claim Now
              </Button>
            </Link>
          </Stack>

          {/* Features */}
          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={8} mt={24}>
            <FeatureCard
              title="Quick Verification"
              description="Verify customer and policy details instantly"
              icon="📄"
            />
            <FeatureCard
              title="AI Damage Analysis"
              description="Advanced image analysis for accurate damage assessment"
              icon="📸"
            />
            <FeatureCard
              title="Fraud Detection"
              description="Cross-verify documents and detect suspicious claims"
              icon="🛡️"
            />
            <FeatureCard
              title="Instant Decision"
              description="Get settlement decisions in minutes, not days"
              icon="✅"
            />
          </SimpleGrid>

          {/* Stats */}
          <Box bg="white" borderRadius="2xl" boxShadow="xl" p={12} mt={24}>
            <SimpleGrid columns={{ base: 1, md: 3 }} gap={8} textAlign="center">
              <Box>
                <Text fontSize="4xl" fontWeight="bold" color="blue.600">90%</Text>
                <Text mt={2} color="gray.600">Faster Processing</Text>
              </Box>
              <Box>
                <Text fontSize="4xl" fontWeight="bold" color="blue.600">40%</Text>
                <Text mt={2} color="gray.600">Cost Reduction</Text>
              </Box>
              <Box>
                <Text fontSize="4xl" fontWeight="bold" color="blue.600">99%</Text>
                <Text mt={2} color="gray.600">Accuracy Rate</Text>
              </Box>
            </SimpleGrid>
          </Box>
        </Container>
      </Box>

      {/* Footer */}
      <Box bg="white" mt={24} borderTopWidth="1px">
        <Container maxW="7xl" py={8}>
          <Text textAlign="center" color="gray.500">
            © 2025 AutoSettled. Powered by AWS Bedrock Agents.
          </Text>
        </Container>
      </Box>
    </Box>
  );
}

function FeatureCard({ icon, title, description }: { icon: string; title: string; description: string }) {
  return (
    <Box bg="white" borderRadius="lg" p={6} boxShadow="md" _hover={{ boxShadow: "xl" }} transition="all 0.2s">
      <Flex justify="center" mb={4}>
        <Text fontSize="4xl">{icon}</Text>
      </Flex>
      <Heading size="md" textAlign="center" mb={2}>{title}</Heading>
      <Text textAlign="center" color="gray.600" fontSize="sm">{description}</Text>
    </Box>
  );
}
