// Tipos y cliente HTTP hacia la API (same-origin vía rewrites de Next).

export interface Negocio {
  id: string;
  slug: string;
  nombre: string;
  greeting: string | null;
  default_reply: string | null;
  activo: boolean;
  autoresponder: boolean;
  created_at: string;
  updated_at: string;
}

export interface Regla {
  id: string;
  negocio_id: string;
  keyword: string;
  respuesta: string;
  posicion: number;
  created_at: string;
}

export interface MensajeChat {
  autor: "visitor" | "bot";
  contenido: string;
  created_at: string;
}

export interface StartResult {
  token: string;
  negocio: { slug: string; nombre: string };
  mensajes: MensajeChat[];
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api${path}`, {
      ...init,
      headers: {
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError(0, "No se pudo conectar con el servidor");
  }

  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      // cuerpo no JSON
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  body: body === undefined ? undefined : JSON.stringify(body),
});

// ── Auth ──────────────────────────────────────────────────────────────
export const login = (email: string, password: string) =>
  request<{ user: { id: string; email: string } }>("/auth/login", json("POST", { email, password }));

export const logout = () => request<{ detail: string }>("/auth/logout", json("POST", undefined));

export const me = () => request<{ id: string; email: string }>("/auth/me");

// ── Negocios ──────────────────────────────────────────────────────────
export const listNegocios = () => request<Negocio[]>("/negocios");

export const createNegocio = (payload: { nombre: string; slug?: string }) =>
  request<Negocio>("/negocios", json("POST", payload));

export const patchNegocio = (id: string, patch: Partial<Negocio>) =>
  request<Negocio>(`/negocios/${id}`, json("PATCH", patch));

export const deleteNegocio = (id: string) => request<void>(`/negocios/${id}`, json("DELETE", undefined));

// ── Reglas ────────────────────────────────────────────────────────────
export const listReglas = (negocioId: string) => request<Regla[]>(`/negocios/${negocioId}/reglas`);

export const createRegla = (negocioId: string, payload: { keyword: string; respuesta: string }) =>
  request<Regla>(`/negocios/${negocioId}/reglas`, json("POST", payload));

export const patchRegla = (reglaId: string, payload: { keyword?: string; respuesta?: string }) =>
  request<Regla>(`/reglas/${reglaId}`, json("PATCH", payload));

export const deleteRegla = (reglaId: string) => request<void>(`/reglas/${reglaId}`, json("DELETE", undefined));

export const reorderReglas = (negocioId: string, reglaIds: string[]) =>
  request<Regla[]>(`/negocios/${negocioId}/reglas/orden`, json("PUT", { regla_ids: reglaIds }));

// ── Chat público ──────────────────────────────────────────────────────
export const startChat = (slug: string) => request<StartResult>(`/public/${slug}/start`);

export const sendMessage = (slug: string, token: string, contenido: string) =>
  request<{ reply: string | null }>(`/public/${slug}/message`, json("POST", { token, contenido }));

export const chatHistory = (slug: string, token: string) =>
  request<MensajeChat[]>(`/public/${slug}/history?token=${encodeURIComponent(token)}`);
