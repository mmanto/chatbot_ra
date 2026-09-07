"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useParams } from "next/navigation";
import { MessageCircle, SendHorizonal } from "lucide-react";

import {
  ApiError,
  chatHistory,
  sendMessage,
  startChat,
  type MensajeChat,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type Estado = "cargando" | "listo" | "no-disponible" | "error";

interface Sesion {
  token: string;
  nombre: string;
}

function keyConv(slug: string) {
  return `ra_conv_${slug}`;
}

function leerSesion(slug: string): Sesion | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(keyConv(slug));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Sesion;
    return typeof parsed.token === "string" && typeof parsed.nombre === "string"
      ? parsed
      : null;
  } catch {
    return null;
  }
}

function guardarSesion(slug: string, sesion: Sesion) {
  window.localStorage.setItem(keyConv(slug), JSON.stringify(sesion));
}

function iniciales(nombre: string) {
  const partes = nombre.trim().split(/\s+/).filter(Boolean);
  if (partes.length === 0) return "?";
  return (partes[0][0] + (partes[1]?.[0] ?? "")).toUpperCase();
}

function hora(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" });
}

export default function ChatPublicoPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;

  const [estado, setEstado] = useState<Estado>("cargando");
  const [token, setToken] = useState<string | null>(null);
  const [nombre, setNombre] = useState("");
  const [mensajes, setMensajes] = useState<MensajeChat[]>([]);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [escribiendo, setEscribiendo] = useState(false);
  const finRef = useRef<HTMLDivElement | null>(null);

  const inicializar = useCallback(async () => {
    setEstado("cargando");
    const previa = leerSesion(slug);
    if (previa) {
      setNombre(previa.nombre);
      try {
        const historial = await chatHistory(slug, previa.token);
        setToken(previa.token);
        setMensajes(historial);
        setEstado("listo");
        document.title = previa.nombre;
        return;
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          setEstado("no-disponible");
          return;
        }
        // Historial fallido por red: reintentar vía start
      }
    }
    try {
      const data = await startChat(slug);
      setToken(data.token);
      setNombre(data.negocio.nombre);
      setMensajes(data.mensajes);
      guardarSesion(slug, { token: data.token, nombre: data.negocio.nombre });
      document.title = data.negocio.nombre;
      setEstado("listo");
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setEstado("no-disponible");
      } else {
        setEstado("error");
      }
    }
  }, [slug]);

  useEffect(() => {
    void inicializar();
  }, [inicializar]);

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [mensajes, escribiendo, estado]);

  async function enviar() {
    const contenido = texto.trim();
    if (!contenido || enviando || !token || estado !== "listo") return;
    setTexto("");
    setEnviando(true);
    // Append optimista del mensaje del visitante
    const optimista: MensajeChat = {
      autor: "visitor",
      contenido,
      created_at: new Date().toISOString(),
    };
    setMensajes((prev) => [...prev, optimista]);
    setEscribiendo(true);
    try {
      const { reply } = await sendMessage(slug, token, contenido);
      if (reply) {
        setMensajes((prev) => [
          ...prev,
          { autor: "bot", contenido: reply, created_at: new Date().toISOString() },
        ]);
      }
    } catch {
      setEscribiendo(false);
      setMensajes((prev) =>
        prev.some((m) => m.created_at === optimista.created_at)
          ? prev
          : [...prev, optimista]
      );
    } finally {
      setEnviando(false);
      setEscribiendo(false);
    }
  }

  if (estado === "no-disponible") {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-muted/40 px-4">
        <div className="text-center">
          <p className="text-lg font-medium">
            Este chat no está disponible por el momento
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            Volvé a intentarlo más tarde.
          </p>
        </div>
      </div>
    );
  }

  if (estado === "error") {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-muted/40 px-4">
        <div className="text-center">
          <p className="text-lg font-medium">No se pudo abrir el chat</p>
          <Button className="mt-4" onClick={() => void inicializar()}>
            Reintentar
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-dvh flex-col bg-muted/40">
      <div className="mx-auto flex h-full w-full max-w-2xl flex-col border-x bg-background">
        {/* Header */}
        <header className="flex items-center gap-3 border-b bg-background px-4 py-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary font-semibold text-primary-foreground">
            {nombre ? iniciales(nombre) : <MessageCircle className="h-5 w-5" />}
          </span>
          <div className="min-w-0">
            <p className="truncate font-semibold leading-tight">
              {nombre || "Cargando…"}
            </p>
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="inline-block h-2 w-2 rounded-full bg-primary" />
              En línea
            </p>
          </div>
        </header>

        {/* Mensajes */}
        <div className="flex-1 space-y-3 overflow-y-auto bg-[#efeae2] p-4">
          {mensajes.map((m, i) => (
            <Burbuja key={`${m.created_at}-${i}`} mensaje={m} />
          ))}
          {escribiendo ? (
            <div className="flex justify-start">
              <div className="flex items-center gap-1 rounded-2xl rounded-bl-md border bg-white px-4 py-3 shadow-sm">
                {[0, 1, 2].map((d) => (
                  <span
                    key={d}
                    className="h-1.5 w-1.5 animate-typing-dot rounded-full bg-muted-foreground"
                    style={{ animationDelay: `${d * 0.15}s` }}
                  />
                ))}
              </div>
            </div>
          ) : null}
          <div ref={finRef} />
        </div>

        {/* Input */}
        <footer className="border-t bg-background p-3">
          <form
            className="flex items-center gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              void enviar();
            }}
          >
            <Input
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              placeholder="Escribí un mensaje"
              maxLength={2000}
              disabled={estado !== "listo" || enviando}
              autoComplete="off"
            />
            <Button
              type="submit"
              size="icon"
              className="h-9 w-9 shrink-0"
              disabled={texto.trim() === "" || enviando || estado !== "listo"}
              aria-label="Enviar"
            >
              <SendHorizonal className="h-4 w-4" />
            </Button>
          </form>
        </footer>
      </div>
    </div>
  );
}

const RE_URL = /https?:\/\/[^\s<>"']+|www\.[^\s<>"']+/gi;

const PUNTUACION_FINAL = ".,;:!?¡¿";
const CIERRES: Record<string, string> = { ")": "(", "]": "[", "}": "{" };

function limpiarUrl(raw: string): string {
  let fin = raw.length;
  while (fin > 0) {
    const c = raw[fin - 1];
    const esCierre = CIERRES[c] !== undefined && !raw.slice(0, fin - 1).includes(CIERRES[c]);
    if (!PUNTUACION_FINAL.includes(c) && !esCierre) break;
    fin--;
  }
  return raw.slice(0, fin);
}

function renderizarContenido(contenido: string, esVisitor: boolean) {
  const nodos: ReactNode[] = [];
  let cursor = 0;
  RE_URL.lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = RE_URL.exec(contenido)) !== null) {
    const idx = match.index;
    if (idx > cursor) nodos.push(contenido.slice(cursor, idx));
    const url = limpiarUrl(match[0]);
    if (url.length > 0) {
      const href = url.startsWith("www.") ? `https://${url}` : url;
      nodos.push(
        <a
          key={idx}
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className={
            esVisitor
              ? "underline underline-offset-2"
              : "text-primary underline underline-offset-2"
          }
        >
          {url}
        </a>
      );
    } else {
      nodos.push(match[0]);
    }
    cursor = idx + match[0].length;
  }
  if (cursor < contenido.length) nodos.push(contenido.slice(cursor));
  return nodos;
}

function Burbuja({ mensaje }: { mensaje: MensajeChat }) {
  const esVisitor = mensaje.autor === "visitor";
  return (
    <div className={esVisitor ? "flex justify-end" : "flex justify-start"}>
      <div
        className={
          esVisitor
            ? "max-w-[80%] rounded-2xl rounded-br-md bg-primary px-3 py-2 text-primary-foreground shadow-sm"
            : "max-w-[80%] rounded-2xl rounded-bl-md border bg-white px-3 py-2 shadow-sm"
        }
      >
        <p className="whitespace-pre-wrap break-words text-sm">
          {renderizarContenido(mensaje.contenido, esVisitor)}
        </p>
        <p
          className={
            esVisitor
              ? "mt-0.5 text-right text-[10px] text-primary-foreground/70"
              : "mt-0.5 text-right text-[10px] text-muted-foreground"
          }
        >
          {hora(mensaje.created_at)}
        </p>
      </div>
    </div>
  );
}
