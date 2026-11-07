-- Cursos de pago (apagado por configuración: PAGOS_ACTIVOS = «no»).
-- Quién tiene acceso a qué curso, y el registro de cada aviso (webhook) que manda la pasarela de pago.

CREATE TABLE acceso_cursos (
  usuario_id INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
  curso      TEXT NOT NULL,                -- el slug del curso, p. ej. «deep-learning»
  origen     TEXT NOT NULL,                -- «pago» | «regalo»
  pedido_id  TEXT,                         -- el pedido que lo dio (si fue un pago)
  desde      INTEGER NOT NULL,
  hasta      INTEGER,                      -- NULL: para siempre; con fecha: se acabó (p. ej. un reembolso)
  PRIMARY KEY (usuario_id, curso)
);

CREATE TABLE pedidos (
  id        TEXT PRIMARY KEY,              -- «proveedor:id del evento»: el mismo aviso dos veces no cuenta dos veces
  proveedor TEXT NOT NULL,                 -- «lemonsqueezy» | «paddle»
  evento    TEXT NOT NULL,                 -- «order_created», «transaction.completed», …
  pedido    TEXT,                          -- id del pedido en la pasarela
  correo    TEXT,
  curso     TEXT,
  efecto    TEXT NOT NULL,                 -- «dar» | «quitar» | «ignorado»
  recibido  INTEGER NOT NULL,
  datos     TEXT NOT NULL                  -- el aviso completo, para revisar a mano
);
