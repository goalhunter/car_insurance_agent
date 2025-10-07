import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
        output.includes('police report') ||
        output.includes('repair estimate')
      ) {
        setClaimState(prev => ({ ...prev, currentStep: ClaimStep.DOCUMENT_ANALYSIS }));
        setShowDamageUpload(false);
        setShowDocumentUpload(true);
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

    const message = `I have uploaded ${uploadedDamageUris.length} damage photo(s). S3 URIs: ${uploadedDamageUris.join(', ')}`;

    await sendMessage(message);
    setIsAnalyzing(false);
  };

  const handleDocumentsDone = async () => {
    setShowDocumentDoneButton(false);
    setIsAnalyzing(true);

    const message = `I have uploaded both documents. Police report URI: ${uploadedPoliceUri}, Repair estimate URI: ${uploadedEstimateUri}`;

    await sendMessage(message);
    setIsAnalyzing(false);

    // Hide upload section after receiving response
    setShowDocumentUpload(false);
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
          <Flex align="center" gap={3}>
            <Text fontSize="2xl">🛡️</Text>
            <Heading size="xl" color="gray.900">File a Claim</Heading>
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
              <Box p={4} borderBottomWidth="1px">
                <Heading size="lg">AI Claims Assistant</Heading>
                <Text fontSize="sm" color="gray.600">
                  I'll guide you through the claims process
                </Text>
              </Box>

              {/* Chat Messages */}
              <Box flex="1" overflowY="auto" p={4}>
                {chatMessages.length === 0 && (
                  <VStack py={12} gap={4}>
                    <Text fontSize="5xl">🛡️</Text>
                    <Heading size="lg">Welcome to AutoSettled</Heading>
                    <Text color="gray.600" maxW="md" textAlign="center">
                      Start by providing your customer ID or email address. I'll help you verify your
                      information and process your claim.
                    </Text>
                  </VStack>
                )}

                <VStack gap={4} align="stretch">
                  {chatMessages.map((message) => (
                    <Flex
                      key={message.id}
                      justify={message.role === 'user' ? 'flex-end' : 'flex-start'}
                    >
                      <Box
                        maxW="80%"
                        bg={message.role === 'user' ? 'blue.600' : 'gray.100'}
                        color={message.role === 'user' ? 'white' : 'gray.900'}
                        borderRadius="lg"
                        px={4}
                        py={2}
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

                          return (
                            <>
                              <Text fontSize="sm" css={{ whiteSpace: 'pre-wrap' }}>
                                {displayContent}
                              </Text>

                              {/* Show PDF download button if message contains PDF URL */}
                              {pdfUrl && message.role === 'assistant' && (
                                <Box mt={3}>
                                  {(() => {
                                    // Update step to Settlement Decision when PDF is available
                                    if (claimState.currentStep !== ClaimStep.SETTLEMENT_DECISION) {
                                      setClaimState(prev => ({ ...prev, currentStep: ClaimStep.SETTLEMENT_DECISION }));
                                    }

                                    return (
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
                                    );
                                  })()}
                                </Box>
                              )}
                            </>
                          );
                        })()}

                        <Text fontSize="xs" mt={1} opacity="0.7">
                          {message.timestamp.toLocaleTimeString()}
                        </Text>
                      </Box>
                    </Flex>
                  ))}

                  {isLoading && (
                    <Flex justify="flex-start">
                      <Box bg="gray.100" borderRadius="lg" px={4} py={2}>
                        <Spinner size="sm" color="gray.600" />
                      </Box>
                    </Flex>
                  )}

                  {/* Show damage image upload at Step 3 */}
                  {showDamageUpload && (
                    <Card.Root bg="blue.50" p={4} borderWidth={2} borderColor="blue.500">
                      <Heading size="sm" mb={3}>📸 Upload Damage Photos</Heading>
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
                      {uploadingFiles.damage && (
                        <HStack mt={2} color="blue.600">
                          <Spinner size="sm" />
                          <Text fontSize="sm">Uploading...</Text>
                        </HStack>
                      )}
                      {claimState.damageImages && claimState.damageImages.length > 0 && (
                        <Badge colorPalette="green" mt={2}>
                          {claimState.damageImages.length} photo(s) uploaded
                        </Badge>
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
                          {uploadingFiles.police && (
                            <HStack mt={2} color="blue.600">
                              <Spinner size="sm" />
                              <Text fontSize="sm">Uploading...</Text>
                            </HStack>
                          )}
                          {claimState.policeReport && (
                            <Badge colorPalette="green" mt={2}>Uploaded ✓</Badge>
                          )}
                        </Box>

                        <Box>
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
                          {uploadingFiles.estimate && (
                            <HStack mt={2} color="blue.600">
                              <Spinner size="sm" />
                              <Text fontSize="sm">Uploading...</Text>
                            </HStack>
                          )}
                          {claimState.repairEstimate && (
                            <Badge colorPalette="green" mt={2}>Uploaded ✓</Badge>
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
