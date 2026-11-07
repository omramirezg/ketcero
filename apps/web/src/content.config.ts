// Contenido del sitio: cursos (orden de temas y lecciones en preparación) y lecciones publicadas (MDX).
import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";

const leccionPendiente = z.object({ titulo: z.string(), estado: z.literal("preparacion") });
const leccionRef = z.object({ slug: z.string() });

const cursos = defineCollection({
  loader: glob({ pattern: "*.json", base: "../../contenido/cursos" }),
  schema: z.object({
    slug: z.string(),
    nombre: z.string(),
    descripcion: z.string(),
    actualizado: z.string(),
    ruta: z.string(),
    // «pago» solo tiene efecto con la API prendida (PAGOS_ACTIVOS y CURSOS_DE_PAGO en apps/api/wrangler.jsonc)
    acceso: z.enum(["gratis", "pago"]).default("gratis"),
    temas: z.array(z.object({
      clave: z.string(),
      titulo: z.string(),
      descripcion: z.string(),
      lecciones: z.array(z.union([leccionRef, leccionPendiente])),
    })),
  }),
});

const lecciones = defineCollection({
  loader: glob({ pattern: "*.mdx", base: "../../contenido/lecciones" }),
  schema: z.object({
    titulo: z.string(),
    slug: z.string(),
    curso: z.string(),
    tema: z.string(),
    numero: z.string(),
    descripcion: z.string(),
    aprender: z.array(z.string()),
    requisitos: z.string(),
    prerrequisitos: z.array(z.string()),
    minutos: z.number(),
    pasos: z.number(),
    datos: z.string(),
    miniatura: z.string(),
    alt: z.string(),
    clip: z.string().optional(),
    animacion: z.object({ fuente: z.string(), fotos: z.union([z.boolean(), z.literal("jpeg")]) }),
    estado: z.enum(["publicada", "borrador", "preparacion"]),
  }),
});

// Lecciones de práctica (fase 1): borradores con ejercicios, no enlazados en los menús hasta revisarlos.
const practica = defineCollection({
  loader: glob({ pattern: "*.mdx", base: "../../contenido/practica" }),
  schema: z.object({
    titulo: z.string(),
    slug: z.string(),
    ruta: z.string(),
    descripcion: z.string(),
    estado: z.enum(["borrador", "publicada"]),
  }),
});

export const collections = { cursos, lecciones, practica };
