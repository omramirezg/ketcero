// Una D1 de mentiras sobre node:sqlite (SQLite en memoria), con la misma forma que usa el Worker:
// prepare().bind().first()/all()/run() y batch(). Así las pruebas corren en segundos y sin Cloudflare.
import { DatabaseSync } from "node:sqlite";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

class Consulta {
  constructor(private db: DatabaseSync, private sql: string, private args: unknown[] = []) {}
  bind(...args: unknown[]) { return new Consulta(this.db, this.sql, args); }
  private st() { return this.db.prepare(this.sql); }
  async first<T>(): Promise<T | null> { return (this.st().get(...(this.args as any[])) as T) ?? null; }
  async all<T>(): Promise<{ results: T[] }> { return { results: this.st().all(...(this.args as any[])) as T[] }; }
  async run() { const r = this.st().run(...(this.args as any[])); return { success: true, meta: { changes: Number(r.changes) } }; }
  correrYa() { return this.st().run(...(this.args as any[])); }
}

export function d1EnMemoria(): D1Database & { sqlite: DatabaseSync } {
  const db = new DatabaseSync(":memory:");
  db.exec("PRAGMA foreign_keys = ON");
  const dir = join(__dirname, "..", "migraciones");
  for (const f of readdirSync(dir).filter((x) => x.endsWith(".sql")).sort()) db.exec(readFileSync(join(dir, f), "utf-8"));
  return {
    sqlite: db,
    prepare: (sql: string) => new Consulta(db, sql),
    batch: async (cs: Consulta[]) => {
      db.exec("BEGIN");
      try { const r = cs.map((c) => c.correrYa()); db.exec("COMMIT"); return r; } catch (e) { db.exec("ROLLBACK"); throw e; }
    },
  } as any;
}
