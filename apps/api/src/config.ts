// Todo lo que se prende o se apaga vive aquí, leído de las variables del Worker (wrangler.jsonc → "vars",
// y los secretos con «wrangler secret put»). Por omisión todo lo que cuesta plata o manda correos está apagado.

export interface Entorno {
  DB: D1Database;
  ASSETS?: Fetcher;
  ORIGEN: string;                 // https://ketcero.com (o http://localhost:8787 en local)
  ENTORNO: string;                // «local» | «produccion»
  CORREO_PROVEEDOR: string;       // «consola» (no manda nada, lo escribe en el registro) | «resend»
  CORREO_REMITENTE?: string;      // «Ket Cero <hola@ketcero.com>»
  RESEND_API_KEY?: string;        // secreto
  TURNSTILE_ACTIVO: string;       // «si» | «no»
  TURNSTILE_SECRETO?: string;     // secreto
  PAGOS_ACTIVOS: string;          // «si» | «no» (fase 3)
  PAGOS_PROVEEDOR?: string;       // «lemonsqueezy» | «paddle»
  LEMONSQUEEZY_SECRETO?: string;  // secreto de la firma del webhook
  PADDLE_SECRETO?: string;        // secreto de la firma del webhook
  STREAM_ACTIVO?: string;         // «si» | «no»
  STREAM_CLAVE_ID?: string;       // id de la clave para firmar tokens de Stream
  STREAM_CLAVE_JWK?: string;      // secreto: la clave privada en JWK (base64)
}

export const activo = (v: string | undefined) => (v ?? "").toLowerCase() === "si";

export const MINUTOS_ENLACE = 15;
export const DIAS_SESION = 30;
export const ENLACES_POR_CORREO_HORA = 5;
export const ENLACES_POR_IP_HORA = 20;
