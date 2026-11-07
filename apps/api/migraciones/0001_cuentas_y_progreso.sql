-- Cuentas sin contraseña (enlace mágico por correo), sesiones y progreso de cada estudiante.
-- Los tokens y las sesiones se guardan como SHA-256: si alguien lee la base, no puede entrar con ellos.

CREATE TABLE usuarios (
  id        INTEGER PRIMARY KEY,
  correo    TEXT NOT NULL UNIQUE,          -- en minúsculas y sin espacios
  creado    INTEGER NOT NULL               -- milisegundos desde 1970
);

CREATE TABLE enlaces (
  token_hash TEXT PRIMARY KEY,
  correo     TEXT NOT NULL,
  ip_hash    TEXT NOT NULL,
  creado     INTEGER NOT NULL,
  expira     INTEGER NOT NULL,
  usado      INTEGER                       -- cuándo se usó; NULL si todavía no
);
CREATE INDEX enlaces_por_correo ON enlaces (correo, creado);
CREATE INDEX enlaces_por_ip ON enlaces (ip_hash, creado);

CREATE TABLE sesiones (
  id_hash    TEXT PRIMARY KEY,
  usuario_id INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
  creado     INTEGER NOT NULL,
  expira     INTEGER NOT NULL
);
CREATE INDEX sesiones_por_usuario ON sesiones (usuario_id);

CREATE TABLE progreso (
  usuario_id  INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
  clave       TEXT NOT NULL,               -- p. ej. «practica:la-derivada-que-usa-una-red/01-derivada-numerica»
  valor       TEXT NOT NULL,               -- JSON pequeño: {"resuelto": true, "bien": 3, "total": 3}
  actualizado INTEGER NOT NULL,            -- gana el más reciente cuando dos dispositivos sincronizan
  PRIMARY KEY (usuario_id, clave)
);
