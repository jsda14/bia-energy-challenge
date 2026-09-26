const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export const apiClient = {
  async get(endpoint: string) {
    return this.request(endpoint, { method: "GET" });
  },

  async post(endpoint: string, body?: unknown) {
    return this.request(endpoint, {
      method: "POST",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  },

  async patch(endpoint: string, body?: unknown) {
    return this.request(endpoint, {
      method: "PATCH",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  },

  async request(endpoint: string, options: RequestInit) {
    const url = `${BASE_URL}${endpoint}`;
    const response = await fetch(url, options);

    if (!response.ok) {
      let errorBody = "";
      try {
        errorBody = await response.text();
      } catch {
        // Ignorar error al leer body
      }
      throw new Error(`HTTP ${response.status}: ${errorBody}`);
    }

    if (response.status === 204) {
      return null;
    }

    return response.json();
  },
};
