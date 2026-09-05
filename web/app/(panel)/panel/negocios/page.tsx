"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, ExternalLink, Pencil, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { deleteNegocio, listNegocios, patchNegocio, type Negocio } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

function enlaceChat(slug: string) {
  return `${window.location.origin}/c/${slug}`;
}

export default function NegociosPage() {
  const queryClient = useQueryClient();
  const [paraEliminar, setParaEliminar] = useState<Negocio | null>(null);

  const { data: negocios, isLoading } = useQuery({
    queryKey: ["negocios"],
    queryFn: listNegocios,
  });

  const invalidar = () => {
    queryClient.invalidateQueries({ queryKey: ["negocios"] });
  };

  const toggleMutation = useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: Partial<Negocio> }) =>
      patchNegocio(id, patch),
    onSuccess: () => {
      invalidar();
      toast.success("Cambio guardado");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Error al guardar"),
  });

  const eliminarMutation = useMutation({
    mutationFn: (id: string) => deleteNegocio(id),
    onSuccess: () => {
      toast.success("Negocio eliminado");
      setParaEliminar(null);
      invalidar();
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Error al eliminar"),
  });

  async function copiar(slug: string) {
    try {
      await navigator.clipboard.writeText(enlaceChat(slug));
      toast.success("Enlace copiado");
    } catch {
      toast.error("No se pudo copiar el enlace");
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Negocios</h1>
          <p className="text-sm text-muted-foreground">
            Cada negocio tiene su enlace de chat y sus reglas de respuesta.
          </p>
        </div>
        <Button asChild>
          <Link href="/panel/negocios/nuevo">
            <Plus className="mr-1 h-4 w-4" />
            Nuevo negocio
          </Link>
        </Button>
      </div>

      <div className="rounded-xl border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nombre</TableHead>
              <TableHead>Slug</TableHead>
              <TableHead>Enlace</TableHead>
              <TableHead className="text-center">Activo</TableHead>
              <TableHead className="text-center">Autoresponder</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="py-8 text-center text-muted-foreground">
                  Cargando…
                </TableCell>
              </TableRow>
            ) : negocios && negocios.length > 0 ? (
              negocios.map((n) => (
                <TableRow key={n.id}>
                  <TableCell className="font-medium">
                    <Link href={`/panel/negocios/${n.id}`} className="hover:underline">
                      {n.nombre}
                    </Link>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{n.slug}</TableCell>
                  <TableCell>
                    <span className="inline-flex items-center gap-1 font-mono text-xs text-muted-foreground">
                      /c/{n.slug}
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        title="Copiar enlace"
                        onClick={() => copiar(n.slug)}
                      >
                        <Copy className="h-3.5 w-3.5" />
                      </Button>
                    </span>
                  </TableCell>
                  <TableCell className="text-center">
                    <Switch
                      checked={n.activo}
                      disabled={toggleMutation.isPending}
                      onCheckedChange={(checked) =>
                        toggleMutation.mutate({ id: n.id, patch: { activo: checked } })
                      }
                      aria-label={`Activar ${n.nombre}`}
                    />
                  </TableCell>
                  <TableCell className="text-center">
                    <Switch
                      checked={n.autoresponder}
                      disabled={toggleMutation.isPending}
                      onCheckedChange={(checked) =>
                        toggleMutation.mutate({ id: n.id, patch: { autoresponder: checked } })
                      }
                      aria-label={`Autoresponder de ${n.nombre}`}
                    />
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="inline-flex items-center gap-1">
                      <Button variant="ghost" size="icon" asChild title="Abrir chat">
                        <a href={`/c/${n.slug}`} target="_blank" rel="noreferrer">
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      </Button>
                      <Button variant="ghost" size="icon" asChild title="Editar">
                        <Link href={`/panel/negocios/${n.id}`}>
                          <Pencil className="h-4 w-4" />
                        </Link>
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Eliminar"
                        className="text-destructive hover:text-destructive"
                        onClick={() => setParaEliminar(n)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={6}
                  className="py-10 text-center text-muted-foreground"
                >
                  Todavía no hay negocios. Creá el primero.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <Dialog open={paraEliminar !== null} onOpenChange={(o) => !o && setParaEliminar(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Eliminar negocio</DialogTitle>
            <DialogDescription>
              Se eliminarán “{paraEliminar?.nombre}”, sus reglas y las conversaciones
              asociadas. Esta acción no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setParaEliminar(null)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              disabled={eliminarMutation.isPending}
              onClick={() => paraEliminar && eliminarMutation.mutate(paraEliminar.id)}
            >
              {eliminarMutation.isPending ? "Eliminando…" : "Eliminar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
