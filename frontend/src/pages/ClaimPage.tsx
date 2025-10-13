import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
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
  VStack,
  HStack,
  SimpleGrid,
  ProgressRoot,
  ProgressTrack,
  ProgressRange,
} from '@chakra-ui/react';
import { ClaimStep, type ClaimState, type ChatMessage } from '../types';
import { invokeAgent, uploadFile, startClaimSession } from '../services/api';

export default function ClaimPage() {
  const navigate = useNavigate();
  const [sessionId, setSessionId] = useState<string>('');
  const [claimState, setClaimState] = useState<ClaimState>({
    currentStep: ClaimStep.CUSTOMER_VERIFICATION,
  });
  const [showDamageUpload, setShowDamageUpload] = useState(false);
  const [showDocumentUpload, setShowDocumentUpload] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<Record<string, boolean>>({});
  const [uploadedDamageUris, setUploadedDamageUris] = useState<string[]>([]);
  const [uploadedPoliceUri, setUploadedPoliceUri] = useState<string>('');
  const [uploadedEstimateUri, setUploadedEstimateUri] = useState<string>('');
  const [showDoneButton, setShowDoneButton] = useState(false);
  const [showDocumentDoneButton, setShowDocumentDoneButton] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // State for file previews
  const [damageImagePreviews, setDamageImagePreviews] = useState<string[]>([]);
  const [policeReportName, setPoliceReportName] = useState<string>('');
  const [estimateName, setEstimateName] = useState<string>('');

  // State to track if a policy button was clicked
  const [policySelected, setPolicySelected] = useState(false);

  // Initialize session on mount
  useEffect(() => {
    startClaimSession()
      .then((res) => setSessionId(res.sessionId))
      .catch(() => {
        // If backend not available, use a mock session ID
        setSessionId('demo-session-' + Date.now());
      });
  }, []);

  const sendMessage = async (message: string) => {
    if (!message.trim() || isLoading) return;

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date(),
    };

    setChatMessages((prev) => [...prev, newMessage]);
    setUserInput('');
    setIsLoading(true);

    try {
      const response = await invokeAgent({
        inputText: message,
        sessionId: sessionId,
        enableTrace: false,
      });

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.output,
        timestamp: new Date(),
      };

      setChatMessages((prev) => [...prev, assistantMessage]);

      // Detect which step we're on based on agent response
      const output = response.output.toLowerCase();

      if (output.includes('step 2') && output.includes('policy')) {
        setClaimState(prev => ({ ...prev, currentStep: ClaimStep.POLICY_VERIFICATION }));
      } else if (
        (output.includes('step 3') && output.includes('damage')) ||
        output.includes('upload photos') ||
        output.includes('upload.*damage') ||
        output.includes('damage.*upload')
      ) {
        setClaimState(prev => ({ ...prev, currentStep: ClaimStep.DAMAGE_ANALYSIS }));
        setShowDamageUpload(true);
      } else if (
        (output.includes('step 4') && output.includes('document')) ||
        output.toLowerCase().includes('police report') ||
        output.toLowerCase().includes('repair estimate') ||
        output.toLowerCase().includes('upload') && output.toLowerCase().includes('documents')
      ) {
        setClaimState(prev => ({ ...prev, currentStep: ClaimStep.DOCUMENT_ANALYSIS }));
        setShowDamageUpload(false);
        setShowDocumentUpload(true);
        // Reset document upload states to allow new uploads
        setShowDocumentDoneButton(false);
        setUploadedPoliceUri('');
        setUploadedEstimateUri('');
        setPoliceReportName('');
        setEstimateName('');
      } else if (
        output.includes('step 5') ||
        output.includes('settlement') ||
        output.includes('final decision') ||
        output.includes('claim decision') ||
        output.includes('approved') ||
        output.includes('denied') ||
        output.includes('manual review')
      ) {
        setClaimState(prev => ({ ...prev, currentStep: ClaimStep.SETTLEMENT_DECISION }));
        setShowDocumentUpload(false);
      }

      // Settlement decision received - no need to navigate, just stay in chat
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Something went wrong'}`,
        timestamp: new Date(),
      };
      setChatMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (files: FileList | null, type: 'damage' | 'police' | 'estimate') => {
    if (!files || files.length === 0) return;

    const fileArray = Array.from(files);
    setUploadingFiles((prev) => ({ ...prev, [type]: true }));

    try {
      // Create previews for images
      if (type === 'damage') {
        const previewPromises = fileArray.map((file) => {
          return new Promise<string>((resolve) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result as string);
            reader.readAsDataURL(file);
          });
        });
        const previews = await Promise.all(previewPromises);
        setDamageImagePreviews((prev) => [...prev, ...previews]);
      } else if (type === 'police') {
        setPoliceReportName(fileArray[0].name);
      } else if (type === 'estimate') {
        setEstimateName(fileArray[0].name);
      }

      const uploadPromises = fileArray.map((file) => uploadFile(file, type));
      const uploadedUris = await Promise.all(uploadPromises);

      // Store URIs and show "Done" button instead of auto-sending
      if (type === 'damage') {
        setUploadedDamageUris((prev) => [...prev, ...uploadedUris]);
        setClaimState((prev) => ({
          ...prev,
          damageImages: [...(prev.damageImages || []), ...uploadedUris],
        }));
        setShowDoneButton(true);
      } else if (type === 'police') {
        setUploadedPoliceUri(uploadedUris[0]);
        setClaimState((prev) => ({ ...prev, policeReport: uploadedUris[0] }));
      } else if (type === 'estimate') {
        setUploadedEstimateUri(uploadedUris[0]);
        setClaimState((prev) => ({ ...prev, repairEstimate: uploadedUris[0] }));
      }

      // Show done button when both documents are uploaded
      if (type === 'police' || type === 'estimate') {
        // Check if both documents are uploaded (considering the one we just uploaded)
        const hasPolice = type === 'police' ? true : !!uploadedPoliceUri;
        const hasEstimate = type === 'estimate' ? true : !!uploadedEstimateUri;

        if (hasPolice && hasEstimate) {
          setShowDocumentDoneButton(true);
        }
      }
    } catch (error) {
      alert(`File upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setUploadingFiles((prev) => ({ ...prev, [type]: false }));
    }
  };

  const handleDoneUploading = async () => {
    setShowDoneButton(false);
    setIsAnalyzing(true);

    // Send message without showing S3 URIs to user
    const message = `I have uploaded ${uploadedDamageUris.length} damage photo(s). S3 URIs: ${uploadedDamageUris.join(', ')}`;

    // Create a user-friendly message that will be shown in chat
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: `✅ Uploaded ${uploadedDamageUris.length} damage photo(s)`,
      timestamp: new Date(),
    };
    setChatMessages((prev) => [...prev, userMessage]);

    // Send actual message with URIs to backend (but user sees friendly message)
    setUserInput('');
    setIsLoading(true);

    try {
      const response = await invokeAgent({
        inputText: message,
        sessionId: sessionId,
        enableTrace: false,
      });

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.output,
        timestamp: new Date(),
      };

      setChatMessages((prev) => [...prev, assistantMessage]);

      // Check AI response and trigger document upload if needed
      const output = response.output.toLowerCase();
      if (
        output.includes('police report') ||
        output.includes('repair estimate') ||
        (output.includes('upload') && output.includes('document'))
      ) {
        setClaimState(prev => ({ ...prev, currentStep: ClaimStep.DOCUMENT_ANALYSIS }));
        setShowDocumentUpload(true);
        setShowDocumentDoneButton(false);
        setUploadedPoliceUri('');
        setUploadedEstimateUri('');
        setPoliceReportName('');
        setEstimateName('');
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Something went wrong'}`,
        timestamp: new Date(),
      };
      setChatMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setIsAnalyzing(false);
      // Hide the damage upload section completely
      setShowDamageUpload(false);
    }
  };

  const handleDocumentsDone = async () => {
    setShowDocumentDoneButton(false);
    setIsAnalyzing(true);

    // Send message without showing S3 URIs to user
    const message = `I have uploaded both documents. Police report URI: ${uploadedPoliceUri}, Repair estimate URI: ${uploadedEstimateUri}`;

    // Create a user-friendly message that will be shown in chat
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: `✅ Uploaded Police Report and Repair Estimate`,
      timestamp: new Date(),
    };
    setChatMessages((prev) => [...prev, userMessage]);

    // Send actual message with URIs to backend (but user sees friendly message)
    setUserInput('');
    setIsLoading(true);

    try {
      const response = await invokeAgent({
        inputText: message,
        sessionId: sessionId,
        enableTrace: false,
      });

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.output,
        timestamp: new Date(),
      };

      setChatMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Something went wrong'}`,
        timestamp: new Date(),
      };
      setChatMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setIsAnalyzing(false);
      // Hide upload section after receiving response
      setShowDocumentUpload(false);
    }
  };

  const getStepInfo = (step: number) => {
    const steps = [
      { title: 'Customer Verification', icon: '✅' },
      { title: 'Policy Verification', icon: '📄' },
      { title: 'Damage Analysis', icon: '📸' },
      { title: 'Document Analysis', icon: '📋' },
      { title: 'Settlement Decision', icon: '🛡️' },
    ];
    return steps[step - 1] || { title: 'Unknown', icon: '❓' };
  };

  const currentStepIndex = claimState.currentStep - 1;
  const progress = ((currentStepIndex + 1) / 5) * 100;

  return (
    <Box minH="100vh" bg="gray.50">
      {/* Header */}
      <Box bg="white" boxShadow="sm" py={4}>
        <Container maxW="7xl">
          <Flex align="center" justify="space-between">
            <Flex align="center" gap={3}>
              <Text fontSize="2xl">🛡️</Text>
              <Heading size="xl" color="gray.900">File a Claim</Heading>
            </Flex>
            <Link to="/">
              <Button variant="ghost" colorPalette="blue" size="sm">
                ← Back to Home
              </Button>
            </Link>
          </Flex>
        </Container>
      </Box>

      <Container maxW="7xl" py={8}>
        <Flex direction={{ base: 'column', lg: 'row' }} gap={8}>
          {/* Left Sidebar - Progress */}
          <Box w={{ base: 'full', lg: '300px' }}>
            {/* Progress Overview */}
            <Card.Root bg="white" p={6} mb={6}>
              <Heading size="md" mb={4}>Progress</Heading>
              <ProgressRoot value={progress} colorPalette="blue" mb={4}>
                <ProgressTrack>
                  <ProgressRange />
                </ProgressTrack>
              </ProgressRoot>
              <Text fontSize="sm" color="gray.600">
                Step {currentStepIndex + 1} of 5
              </Text>
            </Card.Root>

            {/* Steps */}
            <Card.Root bg="white" p={6} mb={6}>
              <Heading size="md" mb={4}>Steps</Heading>
              <VStack gap={3} align="stretch">
                {[1, 2, 3, 4, 5].map((step) => {
                  const stepInfo = getStepInfo(step);
                  const isActive = claimState.currentStep === step;
                  const isCompleted = claimState.currentStep > step;

                  return (
                    <Flex
                      key={step}
                      align="center"
                      gap={3}
                      p={3}
                      borderRadius="lg"
                      bg={isActive ? 'blue.50' : isCompleted ? 'green.50' : 'gray.50'}
                      borderWidth={isActive ? 2 : 0}
                      borderColor={isActive ? 'blue.500' : 'transparent'}
                    >
                      <Text fontSize="xl">{stepInfo.icon}</Text>
                      <Text
                        fontSize="sm"
                        fontWeight="medium"
                        color={isActive ? 'blue.900' : isCompleted ? 'green.900' : 'gray.500'}
                      >
                        {stepInfo.title}
                      </Text>
                    </Flex>
                  );
                })}
              </VStack>
            </Card.Root>

          </Box>

          {/* Right Side - Chat Interface */}
          <Box flex="1">
            <Card.Root bg="white" h="calc(100vh - 12rem)" display="flex" flexDirection="column">
              {/* Chat Header */}
              <Box p={4} borderBottomWidth="1px" bg="gradient-to-r(from-blue.50, to-indigo.50)">
                <Flex align="center" gap={3}>
                  <Flex
                    w={12}
                    h={12}
                    borderRadius="full"
                    bg="blue.500"
                    color="white"
                    align="center"
                    justify="center"
                    fontSize="2xl"
                    boxShadow="md"
                  >
                    🤖
                  </Flex>
                  <Box>
                    <Heading size="lg" color="gray.900">AI Claims Assistant</Heading>
                    <Flex align="center" gap={2}>
                      <Box w={2} h={2} borderRadius="full" bg="green.500" />
                      <Text fontSize="sm" color="gray.600">
                        Online • Ready to help
                      </Text>
                    </Flex>
                  </Box>
                </Flex>
              </Box>

              {/* Chat Messages */}
              <Box flex="1" overflowY="auto" p={4}>
                {chatMessages.length === 0 && (
                  <VStack py={12} gap={6}>
                    <Flex
                      w={20}
                      h={20}
                      borderRadius="full"
                      bg="blue.500"
                      color="white"
                      align="center"
                      justify="center"
                      fontSize="4xl"
                      boxShadow="xl"
                    >
                      🤖
                    </Flex>
                    <Heading size="lg" color="gray.900">Welcome to AutoSettled AI</Heading>
                    <Text color="gray.600" maxW="md" textAlign="center" fontSize="md">
                      👋 Hi! I'm your AI claims assistant. I'll guide you through filing your claim in just <strong>5 simple steps</strong>.
                    </Text>
                    <Box bg="blue.50" p={4} borderRadius="lg" maxW="md">
                      <Text fontSize="sm" color="gray.700" textAlign="center">
                        💡 <strong>Quick tip:</strong> Have your policy details and photos of the damage ready. This process takes about <strong>2 minutes</strong>.
                      </Text>
                    </Box>

                    {/* Quick Start Suggestions */}
                    <VStack gap={3} maxW="md" w="full" mt={4}>
                      <Text fontSize="sm" color="gray.600" fontWeight="medium">
                        Quick start:
                      </Text>
                      <Flex gap={2} flexWrap="wrap" justify="center">
                        <Button
                          onClick={() => sendMessage('Hi, I want to file a claim')}
                          colorPalette="blue"
                          variant="outline"
                          size="sm"
                          leftIcon={<span>👋</span>}
                        >
                          Start My Claim
                        </Button>
                        <Button
                          onClick={() => sendMessage('Hello, I need help with a car accident claim')}
                          colorPalette="blue"
                          variant="outline"
                          size="sm"
                          leftIcon={<span>🚗</span>}
                        >
                          Car Accident Claim
                        </Button>
                        <Button
                          onClick={() => sendMessage('Hi there')}
                          colorPalette="blue"
                          variant="outline"
                          size="sm"
                          leftIcon={<span>💬</span>}
                        >
                          Just Say Hi
                        </Button>
                      </Flex>
                    </VStack>
                  </VStack>
                )}

                <VStack gap={4} align="stretch">
                  {chatMessages.map((message) => (
                    <Flex
                      key={message.id}
                      justify={message.role === 'user' ? 'flex-end' : 'flex-start'}
                      gap={3}
                    >
                      {/* Avatar for assistant messages */}
                      {message.role === 'assistant' && (
                        <Flex
                          w={10}
                          h={10}
                          borderRadius="full"
                          bg="blue.500"
                          color="white"
                          align="center"
                          justify="center"
                          fontSize="xl"
                          flexShrink={0}
                        >
                          🤖
                        </Flex>
                      )}

                      <Box
                        maxW="75%"
                        bg={message.role === 'user' ? 'blue.600' : 'white'}
                        color={message.role === 'user' ? 'white' : 'gray.900'}
                        borderRadius="2xl"
                        px={4}
                        py={3}
                        boxShadow={message.role === 'assistant' ? 'md' : 'sm'}
                        borderWidth={message.role === 'assistant' ? 1 : 0}
                        borderColor="gray.200"
                      >
                        {(() => {
                          // Extract PDF URL and remove it from message content
                          const markdownMatch = message.content.match(/\[.*?\]\((https?:\/\/[^\s)]+)\)/);
                          const plainMatch = message.content.match(/Download your settlement report:\s*(https?:\/\/[^\s]+)/);

                          const pdfUrl = markdownMatch?.[1] || plainMatch?.[1];

                          // Remove the markdown link or plain URL from content
                          let displayContent = message.content;
                          if (markdownMatch) {
                            displayContent = displayContent.replace(markdownMatch[0], '').trim();
                          } else if (plainMatch) {
                            displayContent = displayContent.replace(plainMatch[0], '').trim();
                          }

                          // Format message content with better styling
                          const formatMessage = (content: string) => {
                            // Split by lines for better formatting
                            const lines = content.split('\n');

                            // Check if this is a policy selection message
                            const isPolicySelection = content.includes('Which vehicle was involved in the accident');
                            const policyOptions: string[] = [];

                            if (isPolicySelection) {
                              // Extract policy options (1️⃣, 2️⃣, 3️⃣)
                              lines.forEach(line => {
                                if (line.match(/^[1-3]️⃣/)) {
                                  policyOptions.push(line);
                                }
                              });
                            }

                            return lines.map((line, idx) => {
                              // Skip policy option lines if we're showing buttons
                              if (isPolicySelection && line.match(/^[1-3]️⃣/)) {
                                return null;
                              }

                              // Detect numbered lists (for non-policy messages)
                              if (!isPolicySelection && (line.match(/^[1-3]️⃣/) || line.match(/^[1-3]\./))) {
                                return (
                                  <Box
                                    key={idx}
                                    p={2}
                                    my={1}
                                    bg={message.role === 'user' ? 'blue.700' : 'blue.50'}
                                    borderRadius="md"
                                    borderLeftWidth={3}
                                    borderLeftColor="blue.500"
                                  >
                                    <Text fontSize="sm" fontWeight="medium">{line}</Text>
                                  </Box>
                                );
                              }

                              // Detect section headers (##, Step, etc.)
                              if (line.match(/^##/) || line.match(/^Step \d/)) {
                                return (
                                  <Text key={idx} fontSize="md" fontWeight="bold" mt={2} mb={1} color={message.role === 'user' ? 'white' : 'blue.700'}>
                                    {line.replace(/^##\s*/, '')}
                                  </Text>
                                );
                              }

                              // Regular line
                              if (line.trim()) {
                                return <Text key={idx} fontSize="sm" mb={1}>{line}</Text>;
                              }

                              return <Box key={idx} h={2} />;
                            });
                          };

                          // Check if this message has policy options to show as buttons
                          const isPolicySelection = displayContent.includes('Which vehicle was involved in the accident');
                          const policyOptions: Array<{ number: string; text: string }> = [];

                          if (isPolicySelection) {
                            const lines = displayContent.split('\n');
                            lines.forEach(line => {
                              const match = line.match(/^([1-3])️⃣\s*(.+)/);
                              if (match) {
                                policyOptions.push({ number: match[1], text: match[2] });
                              }
                            });
                          }

                          return (
                            <>
                              <Box>
                                {formatMessage(displayContent)}
                              </Box>

                              {/* Show policy selection buttons */}
                              {isPolicySelection && policyOptions.length > 0 && message.role === 'assistant' && (
                                <VStack gap={2} mt={3} align="stretch">
                                  {policyOptions.map((option) => (
                                    <Button
                                      key={option.number}
                                      onClick={() => {
                                        setPolicySelected(true);
                                        setUserInput(option.number);
                                        sendMessage(option.number);
                                      }}
                                      disabled={policySelected || isLoading}
                                      variant="outline"
                                      colorPalette="blue"
                                      size="md"
                                      textAlign="left"
                                      justifyContent="flex-start"
                                      h="auto"
                                      py={3}
                                      px={4}
                                      whiteSpace="normal"
                                      _hover={!policySelected && !isLoading ? { bg: 'blue.50', borderColor: 'blue.500' } : {}}
                                      opacity={policySelected || isLoading ? 0.5 : 1}
                                      cursor={policySelected || isLoading ? 'not-allowed' : 'pointer'}
                                    >
                                      <Flex align="center" gap={3} w="full">
                                        <Flex
                                          w={8}
                                          h={8}
                                          borderRadius="full"
                                          bg="blue.500"
                                          color="white"
                                          align="center"
                                          justify="center"
                                          fontWeight="bold"
                                          flexShrink={0}
                                        >
                                          {option.number}
                                        </Flex>
                                        <Text fontSize="sm" flex="1">{option.text}</Text>
                                      </Flex>
                                    </Button>
                                  ))}
                                </VStack>
                              )}

                              {/* Show PDF download button if message contains PDF URL */}
                              {pdfUrl && message.role === 'assistant' && (
                                <VStack gap={2} mt={3} align="stretch">
                                  {(() => {
                                    // Update step to Settlement Decision when PDF is available
                                    if (claimState.currentStep !== ClaimStep.SETTLEMENT_DECISION) {
                                      setClaimState(prev => ({ ...prev, currentStep: ClaimStep.SETTLEMENT_DECISION }));
                                    }

                                    return (
                                      <>
                                        <Button
                                          as="a"
                                          href={pdfUrl}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          colorPalette="blue"
                                          size="sm"
                                          w="full"
                                        >
                                          📄 Download Settlement Report (PDF)
                                        </Button>
                                        <Button
                                          onClick={() => navigate('/')}
                                          colorPalette="green"
                                          variant="outline"
                                          size="sm"
                                          w="full"
                                        >
                                          🏠 Back to Home
                                        </Button>
                                      </>
                                    );
                                  })()}
                                </VStack>
                              )}
                            </>
                          );
                        })()}

                        <Text fontSize="xs" mt={1} opacity="0.7">
                          {message.timestamp.toLocaleTimeString()}
                        </Text>
                      </Box>

                      {/* Avatar for user messages */}
                      {message.role === 'user' && (
                        <Flex
                          w={10}
                          h={10}
                          borderRadius="full"
                          bg="blue.600"
                          color="white"
                          align="center"
                          justify="center"
                          fontSize="xl"
                          flexShrink={0}
                        >
                          👤
                        </Flex>
                      )}
                    </Flex>
                  ))}

                  {isLoading && (
                    <Flex justify="flex-start" gap={3}>
                      {/* AI Avatar */}
                      <Flex
                        w={10}
                        h={10}
                        borderRadius="full"
                        bg="blue.500"
                        color="white"
                        align="center"
                        justify="center"
                        fontSize="xl"
                        flexShrink={0}
                      >
                        🤖
                      </Flex>

                      <Box bg="white" borderRadius="2xl" px={4} py={3} boxShadow="md" borderWidth={1} borderColor="gray.200">
                        <HStack gap={2}>
                          <Spinner size="sm" color="blue.600" />
                          <Text fontSize="sm" color="gray.600" fontStyle="italic">
                            AI is analyzing...
                          </Text>
                        </HStack>
                      </Box>
                    </Flex>
                  )}

                  {/* Show damage image upload at Step 3 */}
                  {showDamageUpload && (
                    <Card.Root bg="blue.50" p={4} borderWidth={2} borderColor="blue.500">
                      <Heading size="sm" mb={3}>📸 Upload Damage Photos</Heading>

                      {/* Show upload input unless analysis has started */}
                      {!isAnalyzing && (
                        <>
                          <Text fontSize="sm" mb={3} color="gray.700">
                            Please upload clear photos of the damage to your vehicle
                          </Text>
                          <Input
                            type="file"
                            multiple
                            accept="image/*"
                            onChange={(e) => handleFileUpload(e.target.files, 'damage')}
                            disabled={uploadingFiles.damage}
                            bg="white"
                          />
                        </>
                      )}

                      {uploadingFiles.damage && (
                        <HStack mt={2} color="blue.600">
                          <Spinner size="sm" />
                          <Text fontSize="sm">Uploading...</Text>
                        </HStack>
                      )}
                      {/* Image Previews */}
                      {damageImagePreviews.length > 0 && (
                        <Box mt={3}>
                          <Flex justify="space-between" align="center" mb={2}>
                            <Text fontSize="sm" fontWeight="medium" color="gray.700">
                              📷 Uploaded Photos ({damageImagePreviews.length})
                            </Text>
                            {(isAnalyzing || !showDoneButton) && (
                              <Badge colorPalette="green" size="sm">Confirmed ✓</Badge>
                            )}
                          </Flex>
                          <SimpleGrid columns={{ base: 2, md: 3 }} gap={2}>
                            {damageImagePreviews.map((preview, idx) => (
                              <Box
                                key={idx}
                                position="relative"
                                borderRadius="md"
                                overflow="hidden"
                                borderWidth={2}
                                borderColor="green.500"
                                bg="white"
                              >
                                <img
                                  src={preview}
                                  alt={`Damage ${idx + 1}`}
                                  style={{
                                    width: '100%',
                                    height: '120px',
                                    objectFit: 'cover'
                                  }}
                                />
                                <Badge
                                  position="absolute"
                                  top={1}
                                  right={1}
                                  colorPalette="green"
                                  size="sm"
                                >
                                  ✓
                                </Badge>
                              </Box>
                            ))}
                          </SimpleGrid>
                        </Box>
                      )}
                      {showDoneButton && (
                        <Button
                          mt={3}
                          colorPalette="blue"
                          onClick={handleDoneUploading}
                          w="full"
                        >
                          Done Uploading - Start Analysis
                        </Button>
                      )}
                      {isAnalyzing && (
                        <Box mt={3} p={3} bg="white" borderRadius="md">
                          <HStack mb={2}>
                            <Spinner size="sm" color="blue.600" />
                            <Text fontSize="sm" fontWeight="medium" color="blue.900">
                              Analyzing damage...
                            </Text>
                          </HStack>
                          <ProgressRoot value={undefined} colorPalette="blue" size="sm">
                            <ProgressTrack>
                              <ProgressRange />
                            </ProgressTrack>
                          </ProgressRoot>
                        </Box>
                      )}
                    </Card.Root>
                  )}

                  {/* Show document upload at Step 4 */}
                  {showDocumentUpload && (
                    <Card.Root bg="green.50" p={4} borderWidth={2} borderColor="green.500">
                      <Heading size="sm" mb={3}>📄 Upload Documents</Heading>
                      <VStack gap={3} align="stretch">
                        <Box>
                          {/* Show upload input unless analysis has started */}
                          {!isAnalyzing && (
                            <>
                              <Text fontSize="sm" fontWeight="medium" mb={2}>
                                Police Report (PDF)
                              </Text>
                              <Input
                                type="file"
                                accept=".pdf"
                                onChange={(e) => handleFileUpload(e.target.files, 'police')}
                                disabled={uploadingFiles.police}
                                bg="white"
                              />
                            </>
                          )}
                          {uploadingFiles.police && (
                            <HStack mt={2} color="blue.600">
                              <Spinner size="sm" />
                              <Text fontSize="sm">Uploading...</Text>
                            </HStack>
                          )}
                          {policeReportName && (
                            <Box mt={2} p={2} bg="green.50" borderRadius="md" borderWidth={1} borderColor="green.500">
                              <Flex align="center" gap={2}>
                                <Text fontSize="2xl">📄</Text>
                                <Box flex={1}>
                                  <Text fontSize="xs" fontWeight="medium" color="green.800">
                                    {policeReportName}
                                  </Text>
                                </Box>
                                <Badge colorPalette="green" size="sm">✓</Badge>
                              </Flex>
                            </Box>
                          )}
                        </Box>

                        <Box>
                          {/* Show upload input unless analysis has started */}
                          {!isAnalyzing && (
                            <>
                              <Text fontSize="sm" fontWeight="medium" mb={2}>
                                Repair Estimate (PDF)
                              </Text>
                              <Input
                                type="file"
                                accept=".pdf"
                                onChange={(e) => handleFileUpload(e.target.files, 'estimate')}
                                disabled={uploadingFiles.estimate}
                                bg="white"
                              />
                            </>
                          )}
                          {uploadingFiles.estimate && (
                            <HStack mt={2} color="blue.600">
                              <Spinner size="sm" />
                              <Text fontSize="sm">Uploading...</Text>
                            </HStack>
                          )}
                          {estimateName && (
                            <Box mt={2} p={2} bg="green.50" borderRadius="md" borderWidth={1} borderColor="green.500">
                              <Flex align="center" gap={2}>
                                <Text fontSize="2xl">📄</Text>
                                <Box flex={1}>
                                  <Text fontSize="xs" fontWeight="medium" color="green.800">
                                    {estimateName}
                                  </Text>
                                </Box>
                                <Badge colorPalette="green" size="sm">✓</Badge>
                              </Flex>
                            </Box>
                          )}
                        </Box>
                      </VStack>
                      {showDocumentDoneButton && (
                        <Button
                          mt={3}
                          colorPalette="green"
                          onClick={handleDocumentsDone}
                          w="full"
                        >
                          Done Uploading - Start Analysis
                        </Button>
                      )}
                      {isAnalyzing && (
                        <Box mt={3} p={3} bg="white" borderRadius="md">
                          <HStack mb={2}>
                            <Spinner size="sm" color="green.600" />
                            <Text fontSize="sm" fontWeight="medium" color="green.900">
                              Analyzing documents...
                            </Text>
                          </HStack>
                          <ProgressRoot value={undefined} colorPalette="green" size="sm">
                            <ProgressTrack>
                              <ProgressRange />
                            </ProgressTrack>
                          </ProgressRoot>
                        </Box>
                      )}
                    </Card.Root>
                  )}
                </VStack>
              </Box>

              {/* Chat Input */}
              <Box p={4} borderTopWidth="1px">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    sendMessage(userInput);
                  }}
                >
                  <Flex gap={2}>
                    <Input
                      value={userInput}
                      onChange={(e) => setUserInput(e.target.value)}
                      placeholder="Type your message..."
                      disabled={isLoading}
                      flex="1"
                    />
                    <Button
                      type="submit"
                      disabled={isLoading || !userInput.trim()}
                      colorPalette="blue"
                      px={6}
                    >
                      Send
                    </Button>
                  </Flex>
                </form>
              </Box>
            </Card.Root>
          </Box>
        </Flex>
      </Container>
    </Box>
  );
}
