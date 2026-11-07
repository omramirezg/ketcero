// Envío del enlace de entrada. En local (y mientras no haya cuenta de correo) el proveedor es «consola»:
// el enlace se escribe en el registro del Worker y no sale ningún correo.
import type { Entorno } from "./config";

export interface Mensaje { para: string; asunto: string; texto: string }

export async function enviar(env: Entorno, m: Mensaje): Promise<void> {
  const proveedor = (env.CORREO_PROVEEDOR || "consola").toLowerCase();
  if (proveedor === "consola") {
    console.log(`[correo de prueba] para ${m.para} · ${m.asunto}\n${m.texto}`);
    return;
  }
  if (proveedor === "resend") {
    if (!env.RESEND_API_KEY || !env.CORREO_REMITENTE) throw new Error("Falta RESEND_API_KEY o CORREO_REMITENTE");
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, "Content-Type": "application/json" },
      body: JSON.stringify({ from: env.CORREO_REMITENTE, to: [m.para], subject: m.asunto, text: m.texto }),
    });
    if (!r.ok) throw new Error(`Resend respondió ${r.status}`);
    return;
  }
  throw new Error(`Proveedor de correo desconocido: ${proveedor}`);
}

export function mensajeDeEntrada(enlace: string): { asunto: string; texto: string } {
  return {
    asunto: "Tu enlace para entrar a Ket Cero",
    texto: [
      "Hola:",
      "",
      "Para entrar a Ket Cero abre este enlace (sirve una sola vez y vence en 15 minutos):",
      "",
      enlace,
      "",
      "Si no lo pediste, ignora este correo: nadie puede entrar sin abrirlo.",
      "",
      "Omar · ketcero.com",
    ].join("\n"),
  };
}
