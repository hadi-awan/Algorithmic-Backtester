import type { BacktestRequest, BacktestResponse } from "../types";

const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) {
      // FastAPI/pydantic validation errors: a list of {loc, msg, ...}
      return body.detail
        .map((d: { loc?: unknown[]; msg?: string }) => {
          const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : undefined;
          return field ? `${field}: ${d.msg}` : d.msg;
        })
        .filter(Boolean)
        .join("; ");
    }
  } catch {
    // response body wasn't JSON -- fall through to a generic message
  }
  return `Request failed with status ${response.status}.`;
}

export async function runBacktest(payload: BacktestRequest): Promise<BacktestResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/backtest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError(0, `Could not reach the backend at ${API_URL}. Is it running?`);
  }

  if (!response.ok) {
    const detail = await parseErrorDetail(response);
    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as BacktestResponse;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}
