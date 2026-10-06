export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    public readonly data: unknown,
  ) {
    super(code);
  }
}

type RequestOptions = { headers?: Record<string, string> };

export class HttpClient {
  constructor(
    private readonly baseUrl: string,
    private readonly defaultHeaders: () => Record<string, string> = () => ({}),
  ) {}

  get<T>(path: string, options?: RequestOptions) {
    return this.request<T>("GET", path, undefined, options);
  }

  post<T>(path: string, body?: unknown, options?: RequestOptions) {
    return this.request<T>("POST", path, body, options);
  }

  patch<T>(path: string, body?: unknown, options?: RequestOptions) {
    return this.request<T>("PATCH", path, body, options);
  }

  delete<T>(path: string, options?: RequestOptions) {
    return this.request<T>("DELETE", path, undefined, options);
  }

  async postForm<T>(
    path: string,
    form: FormData,
    options?: RequestOptions,
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      // No Content-Type: fetch sets the multipart boundary itself.
      headers: { ...this.defaultHeaders(), ...options?.headers },
      body: form,
    });
    return this.handle<T>(response);
  }

  private async request<T>(
    method: string,
    path: string,
    body: unknown,
    options?: RequestOptions,
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...this.defaultHeaders(),
        ...options?.headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    return this.handle<T>(response);
  }

  private async handle<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const data = await response.json().catch(() => undefined);
      const code =
        typeof data === "object" && data !== null && "code" in data
          ? String((data as { code: unknown }).code)
          : "unknown_error";
      throw new ApiError(response.status, code, data);
    }
    if (response.status === 204) {
      return undefined as T;
    }
    return response.json() as Promise<T>;
  }
}
