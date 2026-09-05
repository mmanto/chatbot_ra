"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";

import { ApiError, createNegocio } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const SLUG_PATTERN = /^[a-z0-9]+(-[a-z0-9]+)*$/;

export default function NuevoNegocioPage() {
  const router = useRouter();
  const [nombre, setNombre] = useState("");
  const [slug, setSlug] = useState("");
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      createNegocio({ nombre, slug: slug.trim() === "" ? undefined : slug.trim() }),
    onSuccess: (negocio) => {
      router.push(`/panel/negocios/${negocio.id}`);
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 409) {
        setError("El slug ya está en uso. Probá otro.");
      } else {
        setError(err instanceof Error ? err.message : "Error al crear el negocio");
      }
    },
  });

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (slug.trim() !== "" && !SLUG_PATTERN.test(slug.trim())) {
      setError("El slug solo puede tener minúsculas, números y guiones entre palabras.");
      return;
    }
    setError(null);
    mutation.mutate();
  }

  return (
    <div className="mx-auto max-w-xl space-y-4">
      <Button variant="ghost" size="sm" onClick={() => router.push("/panel/negocios")}>
        <ArrowLeft className="mr-1 h-4 w-4" />
        Volver
      </Button>
      <Card>
        <CardHeader>
          <CardTitle>Nuevo negocio</CardTitle>
          <CardDescription>
            Si dejás el slug vacío se genera automáticamente a partir del nombre.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="nombre">Nombre</Label>
              <Input
                id="nombre"
                required
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                placeholder="Panadería La Aurora"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="slug">Slug (opcional)</Label>
              <Input
                id="slug"
                value={slug}
                onChange={(e) => setSlug(e.target.value.toLowerCase())}
                placeholder="panaderia-la-aurora"
              />
              <p className="text-xs text-muted-foreground">
                Aparecerá en el enlace del chat: /c/tu-slug
              </p>
            </div>
            {error ? (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            ) : null}
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Creando…" : "Crear negocio"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
