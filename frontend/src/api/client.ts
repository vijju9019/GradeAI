const API_BASE = '/api/v1';

export class ApiError extends Error {
  status: number;
  data: any;
  constructor(status: number, message: string, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('gradeai_token');
  const headers = new Headers(options.headers || {});

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = 'Request failed';
    let data;
    try {
      data = await response.json();
      errorDetail = data.detail || data.message || errorDetail;
    } catch {
      errorDetail = await response.text();
    }
    throw new ApiError(response.status, errorDetail, data);
  }

  // Handle binary / blob downloads
  const contentType = response.headers.get('content-type') || '';
  if (
    contentType.includes('application/pdf') ||
    contentType.includes('text/csv') ||
    contentType.includes('application/vnd.openxmlformats') ||
    contentType.includes('octet-stream')
  ) {
    return (await response.blob()) as unknown as T;
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}
