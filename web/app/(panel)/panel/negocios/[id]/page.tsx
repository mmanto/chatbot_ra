"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Check,
  Copy,
  ExternalLink,
  Loader2,
  Plus,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";

import {
  ApiError,
  createRegla,
  deleteRegla,
  listNegocios,
  listReglas,
  patchNegocio,
  patchRegla,
  reorderReglas,
  type Negocio,
  type Regla,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";

const SLUG_PATTERN = /^[a-z0-9]+(-[a-z0-9]+)*$/;

function useNegocio(id: string) {
  const queryClient = useQueryClient();
  const { data: negocios } = useQuery({ queryKey: ["negocios"], queryFn: listNegocios });
  const negocio = negocios?.find((n) => n.id === id);

  const invalidar = (keys: string[][]) => {
    keys.forEach((k) => queryClient.invalidateQueries({ queryKey: k }));
  };

  return { negocio, invalidar };
}

export default function NegocioDetallePage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const { negocio, invalidar } = useNegocio(id);

  const { data: reglas, isLoading: reglasCargando } = useQuery({
    queryKey: ["reglas", id],
    queryFn: () => listReglas(id),
    enabled: Boolean(id),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" asChild title="Volver">
            <a href="/panel/negocios">
              <ArrowLeft className="h-4 w-4" />
            </a>
          </Button>
          <h1 className="text-2xl font-semibold tracking-tight">
            {negocio ? negocio.nombre : "Negocio"}
          </h1>
        </div>
      </div>

      <DatosCard negocio={negocio} invalidar={invalidar} />
      <AutoresponderCard negocio={negocio} invalidar={invalidar} />
      <ReglasCard
        negocioId={id}
        reglas={reglas ?? []}
        cargando={reglasCargando}
        invalidar={invalidar}
      />
      <EnlaceCard negocio={negocio} />
    </div>
  );
}

function DatosCard({
  negocio,
  invalidar,
}: {
  negocio: Negocio | undefined;
  invalidar: (keys: string[][]) => void;
}) {
  const [nombre, setNombre] = useState("");
  const [slug, setSlug] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (negocio) {
      setNombre(negocio.nombre);
      setSlug(negocio.slug);
      setError(null);
    }
  }, [negocio]);

  const mutation = useMutation({
    mutationFn: () => patchNegocio(negocio!.id, { nombre, slug }),
    onSuccess: () => {
      toast.success("Datos guardados");
      invalidar([["negocios"], ["negocio", negocio!.id]]);
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 409) {
        setError("El slug ya está en uso.");
      } else {
        setError(err instanceof Error ? err.message : "Error al guardar");
      }
    },
  });

  function guardar(e: React.FormEvent) {
    e.preventDefault();
    if (!SLUG_PATTERN.test(slug)) {
      setError("El slug solo puede tener minúsculas, números y guiones entre palabras.");
      return;
    }
    setError(null);
    mutation.mutate();
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Datos del negocio</CardTitle>
        <CardDescription>Nombre y enlace público del chat.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={guardar} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="nombre">Nombre</Label>
            <Input
              id="nombre"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              disabled={mutation.isPending}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="slug">Slug</Label>
            <Input
              id="slug"
              value={slug}
              onChange={(e) => setSlug(e.target.value.toLowerCase())}
              disabled={mutation.isPending}
            />
            <p className="text-xs text-muted-foreground">
              Define el enlace del chat: /c/{slug || "…"}
            </p>
          </div>
          {error ? (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          ) : null}
          <Button type="submit" disabled={mutation.isPending || !negocio}>
            {mutation.isPending ? "Guardando…" : "Guardar"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function AutoresponderCard({
  negocio,
  invalidar,
}: {
  negocio: Negocio | undefined;
  invalidar: (keys: string[][]) => void;
}) {
  const [greeting, setGreeting] = useState("");
  const [defaultReply, setDefaultReply] = useState("");
  const [guardando, setGuardando] = useState<"greeting" | "default" | null>(null);

  useEffect(() => {
    if (negocio) {
      setGreeting(negocio.greeting ?? "");
      setDefaultReply(negocio.default_reply ?? "");
    }
  }, [negocio]);

  const toggleMutation = useMutation({
    mutationFn: (patch: Partial<Negocio>) => patchNegocio(negocio!.id, patch),
    onSuccess: () => {
      invalidar([["negocios"], ["negocio", negocio!.id]]);
      toast.success("Autoresponder actualizado");
    },
    onError: (err) =>
      toast.error(err instanceof Error ? err.message : "Error al guardar"),
  });

  async function guardarTexto(campo: "greeting" | "default", valor: string) {
    if (!negocio) return;
    setGuardando(campo);
    try {
      await patchNegocio(negocio.id, { [campo]: valor.trim() === "" ? null : valor });
      invalidar([["negocios"], ["negocio", negocio!.id]]);
      toast.success("Guardado");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setGuardando(null);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Autoresponder</CardTitle>
        <CardDescription>
          El bot responde automáticamente dentro del chat web de este negocio.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium">Responder automáticamente</p>
            <p className="text-sm text-muted-foreground">
              Si está apagado, el chat registra los mensajes pero el bot no responde.
            </p>
          </div>
          <Switch
            checked={negocio?.autoresponder ?? false}
            disabled={!negocio || toggleMutation.isPending}
            onCheckedChange={(checked) =>
              toggleMutation.mutate({ autoresponder: checked })
            }
            aria-label="Autoresponder activo"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="greeting">Mensaje de bienvenida al abrir el chat</Label>
          <Textarea
            id="greeting"
            rows={3}
            value={greeting}
            disabled={!negocio}
            onChange={(e) => setGreeting(e.target.value)}
            placeholder="¡Hola! Escribí una palabra clave para empezar…"
          />
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs text-muted-foreground">
              Vacío: no se envía ningún saludo.
            </p>
            <Button
              variant="outline"
              size="sm"
              disabled={!negocio || guardando === "greeting"}
              onClick={() => guardarTexto("greeting", greeting)}
            >
              {guardando === "greeting" ? "Guardando…" : "Guardar saludo"}
            </Button>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="default_reply">
            Respuesta cuando ninguna regla coincide
          </Label>
          <Textarea
            id="default_reply"
            rows={3}
            value={defaultReply}
            disabled={!negocio}
            onChange={(e) => setDefaultReply(e.target.value)}
            placeholder="Gracias por escribirnos. Un asesor te atenderá en breve."
          />
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs text-muted-foreground">
              Vacío: el bot no responde cuando no hay coincidencia.
            </p>
            <Button
              variant="outline"
              size="sm"
              disabled={!negocio || guardando === "default"}
              onClick={() => guardarTexto("default", defaultReply)}
            >
              {guardando === "default" ? "Guardando…" : "Guardar respuesta"}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ReglasCard({
  negocioId,
  reglas,
  cargando,
  invalidar,
}: {
  negocioId: string;
  reglas: Regla[];
  cargando: boolean;
  invalidar: (keys: string[][]) => void;
}) {
  const queryClient = useQueryClient();
  const refetchReglas = () =>
    queryClient.invalidateQueries({ queryKey: ["reglas", negocioId] });

  const mover = (index: number, direccion: -1 | 1) => {
    const nuevo = [...reglas];
    const target = index + direccion;
    if (target < 0 || target >= nuevo.length) return;
    [nuevo[index], nuevo[target]] = [nuevo[target], nuevo[index]];
    reorderMutation.mutate(nuevo.map((r) => r.id));
  };

  const reorderMutation = useMutation({
    mutationFn: (ids: string[]) => reorderReglas(negocioId, ids),
    onSuccess: () => {
      refetchReglas();
      toast.success("Orden actualizado");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Error al ordenar"),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Reglas</CardTitle>
        <CardDescription>
          Si el mensaje del visitante contiene la frase, el bot responde con el texto
          definido. Gana la primera regla que coincida, en el orden de la lista.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {cargando ? (
          <p className="py-4 text-center text-sm text-muted-foreground">Cargando reglas…</p>
        ) : reglas.length === 0 ? (
          <p className="py-4 text-center text-sm text-muted-foreground">
            Sin reglas todavía. Agregá la primera abajo.
          </p>
        ) : (
          reglas.map((regla, i) => (
            <ReglaFila
              key={regla.id}
              regla={regla}
              primero={i === 0}
              ultimo={i === reglas.length - 1}
              moviendo={reorderMutation.isPending}
              onMove={(dir) => mover(i, dir)}
              onGuardado={() => refetchReglas()}
            />
          ))
        )}
        <AñadirRegla negocioId={negocioId} onAgregada={() => refetchReglas()} invalidar={invalidar} />
      </CardContent>
    </Card>
  );
}

function ReglaFila({
  regla,
  primero,
  ultimo,
  moviendo,
  onMove,
  onGuardado,
}: {
  regla: Regla;
  primero: boolean;
  ultimo: boolean;
  moviendo: boolean;
  onMove: (dir: -1 | 1) => void;
  onGuardado: () => void;
}) {
  const [keyword, setKeyword] = useState(regla.keyword);
  const [respuesta, setRespuesta] = useState(regla.respuesta);
  const [guardando, setGuardando] = useState(false);
  const [confirmarDelete, setConfirmarDelete] = useState(false);

  const sucio = keyword !== regla.keyword || respuesta !== regla.respuesta;

  const guardar = async () => {
    if (keyword.trim() === "" || respuesta.trim() === "") return;
    setGuardando(true);
    try {
      await patchRegla(regla.id, { keyword: keyword.trim(), respuesta: respuesta.trim() });
      toast.success("Regla guardada");
      onGuardado();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setGuardando(false);
    }
  };

  const eliminar = async () => {
    try {
      await deleteRegla(regla.id);
      toast.success("Regla eliminada");
      onGuardado();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Error al eliminar");
    }
  };

  return (
    <div className="flex flex-col gap-2 rounded-lg border p-3">
      <div className="flex items-start gap-2">
        <div className="flex flex-col gap-0.5 pt-0.5">
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            disabled={primero || moviendo}
            title="Subir"
            onClick={() => onMove(-1)}
          >
            ↑
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            disabled={ultimo || moviendo}
            title="Bajar"
            onClick={() => onMove(1)}
          >
            ↓
          </Button>
        </div>
        <div className="flex-1 space-y-2">
          <div>
            <Label className="text-xs text-muted-foreground">
              Si el mensaje contiene…
            </Label>
            <Input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="ej: precio"
              maxLength={200}
            />
          </div>
          <div>
            <Label className="text-xs text-muted-foreground">Responder con…</Label>
            <Textarea
              rows={2}
              value={respuesta}
              onChange={(e) => setRespuesta(e.target.value)}
              placeholder="La respuesta del bot"
            />
          </div>
        </div>
      </div>
      <div className="flex items-center justify-end gap-2">
        <Button
          variant="ghost"
          size="sm"
          className="text-destructive hover:text-destructive"
          onClick={() => setConfirmarDelete(true)}
        >
          <Trash2 className="mr-1 h-4 w-4" />
          Eliminar
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={!sucio || guardando || keyword.trim() === "" || respuesta.trim() === ""}
          onClick={guardar}
        >
          {guardando ? (
            <Loader2 className="mr-1 h-4 w-4 animate-spin" />
          ) : (
            <Check className="mr-1 h-4 w-4" />
          )}
          Guardar
        </Button>
      </div>

      <Dialog open={confirmarDelete} onOpenChange={setConfirmarDelete}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Eliminar regla</DialogTitle>
            <DialogDescription>
              Se eliminará la regla “{regla.keyword}”. Esta acción no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmarDelete(false)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                setConfirmarDelete(false);
                void eliminar();
              }}
            >
              Eliminar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function AñadirRegla({
  negocioId,
  onAgregada,
  invalidar,
}: {
  negocioId: string;
  onAgregada: () => void;
  invalidar: (keys: string[][]) => void;
}) {
  const [keyword, setKeyword] = useState("");
  const [respuesta, setRespuesta] = useState("");
  const [agregando, setAgregando] = useState(false);

  const agregar = async () => {
    if (keyword.trim() === "" || respuesta.trim() === "") return;
    setAgregando(true);
    try {
      await createRegla(negocioId, { keyword: keyword.trim(), respuesta: respuesta.trim() });
      setKeyword("");
      setRespuesta("");
      onAgregada();
      invalidar([["negocios"]]);
      toast.success("Regla agregada");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Error al agregar");
    } finally {
      setAgregando(false);
    }
  };

  return (
    <div className="rounded-lg border border-dashed p-3">
      <p className="mb-2 text-xs font-medium text-muted-foreground">Añadir regla</p>
      <div className="space-y-2">
        <Input
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="Si el mensaje contiene… (ej: precio)"
          maxLength={200}
        />
        <Textarea
          rows={2}
          value={respuesta}
          onChange={(e) => setRespuesta(e.target.value)}
          placeholder="Responder con…"
        />
      </div>
      <div className="mt-2 flex justify-end">
        <Button
          variant="secondary"
          size="sm"
          disabled={
            agregando || keyword.trim() === "" || respuesta.trim() === ""
          }
          onClick={agregar}
        >
          {agregando ? (
            <Loader2 className="mr-1 h-4 w-4 animate-spin" />
          ) : (
            <Plus className="mr-1 h-4 w-4" />
          )}
          Añadir
        </Button>
      </div>
    </div>
  );
}

function EnlaceCard({ negocio }: { negocio: Negocio | undefined }) {
  const [origen, setOrigen] = useState("");

  useEffect(() => {
    setOrigen(window.location.origin);
  }, []);

  const enlace = negocio ? `${origen}/c/${negocio.slug}` : "";

  async function copiar() {
    if (!enlace) return;
    try {
      await navigator.clipboard.writeText(enlace);
      toast.success("Enlace copiado");
    } catch {
      toast.error("No se pudo copiar el enlace");
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Enlace público</CardTitle>
        <CardDescription>
          Publicá este enlace donde quieras: el cliente abre el chat y el bot responde.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2">
          <Input readOnly value={enlace || "…"} className="font-mono text-sm" />
          <Button variant="outline" onClick={copiar} disabled={!enlace} title="Copiar">
            <Copy className="h-4 w-4" />
          </Button>
          {negocio ? (
            <Button asChild title="Abrir chat">
              <a href={`/c/${negocio.slug}`} target="_blank" rel="noreferrer">
                <ExternalLink className="mr-1 h-4 w-4" />
                Abrir chat
              </a>
            </Button>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}
