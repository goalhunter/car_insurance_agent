// API Configuration
const API_BASE_URL = 'https://52xcceuza5i7iuwmrri2xfsnoq0etomm.lambda-url.us-east-1.on.aws';
const UPLOAD_API_URL = 'https://ihjp2pdhub.execute-api.us-east-1.amazonaws.com/Prod';

export interface AgentInvokeRequest {
  inputText: string;
  sessionId?: string;
  enableTrace?: boolean;
  sessionState?: Record<string, any>;
}

export interface AgentInvokeResponse {
  sessionId: string;
  output: string;
  trace?: any[];
  completion: string;
}

// Generic API call function
async function apiCall<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }));
    throw new Error(error.message || 'API request failed');
  }

  return response.json();
}

// Upload file to S3
export async function uploadFile(file: File, folder: string): Promise<string> {
  // Convert file to base64
  const fileContent = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = (reader.result as string).split(',')[1]; // Remove data:image/png;base64, prefix
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });

  const response = await fetch(`${UPLOAD_API_URL}/upload`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      fileContent,
      fileName: file.name,
      folder,
      contentType: file.type,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'File upload failed' }));
    throw new Error(error.error || 'File upload failed');
  }

  const data = await response.json();
  return data.uri; // S3 URI
}

// Invoke Bedrock Agent
export async function invokeAgent(request: AgentInvokeRequest): Promise<AgentInvokeResponse> {
  return apiCall<AgentInvokeResponse>('/agent/invoke', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// Start a new claim session
export async function startClaimSession(): Promise<{ sessionId: string }> {
  return apiCall<{ sessionId: string }>('/claim/start', {
    method: 'POST',
  });
}

// Get claim status
export async function getClaimStatus(claimId: string): Promise<any> {
  return apiCall(`/claim/${claimId}`, {
    method: 'GET',
  });
}

// List all claims (for dashboard)
export async function listClaims(limit: number = 50): Promise<any[]> {
  return apiCall(`/claims?limit=${limit}`, {
    method: 'GET',
  });
}
