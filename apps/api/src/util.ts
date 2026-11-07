// Utilidades pequeñas: respuestas JSON, cookies, azar criptográfico y SHA-256.

export const json = (datos: unknown, estado = 200, extra: HeadersInit = {}) =>
  new Response(JSON.stringify(datos), {
    status: estado,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", ...extra },
  });

export const error = (estado: number, mensaje: string) => json({ error: mensaje }, estado);

export function azar(bytes = 32): string {
  const b = crypto.getRandomValues(new Uint8Array(bytes));
  return btoa(String.fromCharCode(...b)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

const hex = (buf: ArrayBuffer) => [...new Uint8Array(buf)].map((x) => x.toString(16).padStart(2, "0")).join("");

export async function sha256(texto: string): Promise<string> {
  return hex(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(texto)));
}

export async function hmacSha256(secreto: string, mensaje: string): Promise<string> {
  const clave = await crypto.subtle.importKey("raw", new TextEncoder().encode(secreto), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return hex(await crypto.subtle.sign("HMAC", clave, new TextEncoder().encode(mensaje)));
}

/** Compara dos textos en tiempo constante (para firmas). */
export function iguales(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

export function leerCookie(req: Request, nombre: string): string | null {
  for (const parte of (req.headers.get("Cookie") ?? "").split(";")) {
    const [k, ...v] = parte.trim().split("=");
    if (k === nombre) return v.join("=");
  }
  return null;
}

export function cookie(nombre: string, valor: string, segundos: number): string {
  return `${nombre}=${valor}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${segundos}`;
}

export const correoValido = (c: string) => c.length <= 254 && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(c);

export const escapar = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
