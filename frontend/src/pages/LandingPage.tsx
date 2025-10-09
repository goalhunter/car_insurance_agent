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
              <Text fontSize="2xl">🚗</Text>
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
            <Text fontSize="6xl" mb={-4}>🚗💨</Text>
            <Heading size="4xl" color="gray.900">
              Car Insurance Claims, Settled in Minutes
            </Heading>
            <Text fontSize="xl" color="gray.600" maxW="3xl">
              File your auto claim instantly with AI-powered damage assessment.
              From fender bender to major collision, get your settlement decision in under 2 minutes.
            </Text>
            <Flex gap={4} flexDirection={{ base: 'column', md: 'row' }}>
              <Link to="/claim">
                <Button size="xl" colorPalette="blue" px={8} py={6} fontSize="lg" boxShadow="lg">
                  🚗 File a Claim Now
                </Button>
              </Link>
              <Link to="/claim">
                <Button size="xl" variant="outline" colorPalette="blue" px={8} py={6} fontSize="lg">
                  🎬 Try Demo Claim
                </Button>
              </Link>
            </Flex>
          </Stack>

          {/* Features */}
          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={8} mt={24}>
            <FeatureCard
              title="Instant Verification"
              description="Verify driver info and policy coverage in seconds"
              icon="👤"
            />
            <FeatureCard
              title="AI Damage Analysis"
              description="Upload photos - AI assesses dents, scratches, and collision damage"
              icon="🔍"
            />
            <FeatureCard
              title="Document Processing"
              description="Police reports & repair estimates analyzed automatically"
              icon="📋"
            />
            <FeatureCard
              title="2-Minute Settlement"
              description="From minor fender bender to major collision - decided instantly"
              icon="⚡"
            />
          </SimpleGrid>

          {/* Stats */}
          <Box bg="white" borderRadius="2xl" boxShadow="xl" p={12} mt={24}>
            <Heading size="lg" textAlign="center" mb={8} color="gray.900">
              Why Choose AutoSettled?
            </Heading>
            <SimpleGrid columns={{ base: 1, md: 3 }} gap={8} textAlign="center">
              <Box>
                <Text fontSize="4xl" fontWeight="bold" color="blue.600">14 Days → 2 Min</Text>
                <Text mt={2} color="gray.600" fontWeight="medium">Average Claim Processing Time</Text>
                <Text mt={1} fontSize="sm" color="gray.500">Traditional vs. AI-powered</Text>
              </Box>
              <Box>
                <Text fontSize="4xl" fontWeight="bold" color="blue.600">40% Less</Text>
                <Text mt={2} color="gray.600" fontWeight="medium">Operational Costs</Text>
                <Text mt={1} fontSize="sm" color="gray.500">Automated damage assessment</Text>
              </Box>
              <Box>
                <Text fontSize="4xl" fontWeight="bold" color="blue.600">99.2%</Text>
                <Text mt={2} color="gray.600" fontWeight="medium">Decision Accuracy</Text>
                <Text mt={1} fontSize="sm" color="gray.500">Multi-modal AI verification</Text>
              </Box>
            </SimpleGrid>
          </Box>
        </Container>
      </Box>

      {/* How It Works */}
      <Box bg="white" py={20}>
        <Container maxW="7xl">
          <Heading size="2xl" textAlign="center" mb={12} color="gray.900">
            How It Works
          </Heading>
          <SimpleGrid columns={{ base: 1, md: 5 }} gap={6}>
            <StepCard number="1" title="Start Claim" description="Enter your customer ID or email" icon="👤" />
            <StepCard number="2" title="Verify Policy" description="We check your coverage automatically" icon="📄" />
            <StepCard number="3" title="Upload Photos" description="Take pictures of car damage" icon="📸" />
            <StepCard number="4" title="Submit Docs" description="Police report & repair estimate" icon="📋" />
            <StepCard number="5" title="Get Decision" description="Instant settlement PDF" icon="✅" />
          </SimpleGrid>
        </Container>
      </Box>

      {/* Footer */}
      <Box bg="gray.900" color="white" py={12}>
        <Container maxW="7xl">
          <Flex justify="space-between" align="center" direction={{ base: 'column', md: 'row' }} gap={4}>
            <Flex align="center" gap={3}>
              <Text fontSize="2xl">🚗</Text>
              <Heading size="lg">AutoSettled</Heading>
            </Flex>
            <Text color="gray.400">
              Powered by AWS Bedrock Agents & Claude 3.7 Sonnet
            </Text>
          </Flex>
          <Text textAlign="center" color="gray.500" mt={8} fontSize="sm">
            © 2025 AutoSettled. All rights reserved.
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

function StepCard({ number, icon, title, description }: { number: string; icon: string; title: string; description: string }) {
  return (
    <Box bg="gray.50" borderRadius="lg" p={6} textAlign="center" borderWidth={2} borderColor="blue.200">
      <Flex justify="center" align="center" mb={3}>
        <Box bg="blue.600" color="white" borderRadius="full" w={10} h={10} display="flex" alignItems="center" justifyContent="center" fontWeight="bold" mr={2}>
          {number}
        </Box>
        <Text fontSize="3xl">{icon}</Text>
      </Flex>
      <Heading size="sm" mb={2} color="gray.900">{title}</Heading>
      <Text fontSize="xs" color="gray.600">{description}</Text>
    </Box>
  );
}
