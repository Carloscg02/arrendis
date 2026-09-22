#!/usr/bin/env python3
"""
Script de utilidad para reiniciar el estado de Onboarding de un usuario (F-28).

Uso:
    python3 scripts/reset_onboarding.py
    python3 scripts/reset_onboarding.py CarlosCanoAdmin
    python3 scripts/reset_onboarding.py --email carloscg.002@gmail.com
    python3 scripts/reset_onboarding.py --completed  (para marcarlo como completado)
"""

import sys
import os
import sqlite3
import argparse
from pathlib import Path

# Raíz del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "data" / "rental.db"))


def reset_onboarding(identifier: str, completed: bool = False) -> None:
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: No se encontró la base de datos en {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Buscar usuario por username o email
    cursor.execute(
        "SELECT id, username, email, onboarding_completed FROM users WHERE username = ? OR LOWER(email) = ?",
        (identifier, identifier.lower()),
    )
    user = cursor.fetchone()

    if not user:
        print(f"⚠️  No se encontró ningún usuario con username o email: '{identifier}'")
        # Mostrar usuarios disponibles
        cursor.execute("SELECT username, email, onboarding_completed FROM users")
        all_users = cursor.fetchall()
        if all_users:
            print("\nUsuarios registrados en la base de datos:")
            for u in all_users:
                status_str = "✅ Completado" if u["onboarding_completed"] else "⏳ Pendiente"
                print(f"  - {u['username']} ({u['email']}) -> {status_str}")
        conn.close()
        sys.exit(1)

    user_id = user["id"]
    new_status = 1 if completed else 0

    # Actualizar estado
    cursor.execute(
        "UPDATE users SET onboarding_completed = ? WHERE id = ?",
        (new_status, user_id),
    )
    conn.commit()

    action = "marcado como COMPLETADO" if completed else "REINICIADO (pendiente)"
    print("\n" + "=" * 60)
    print(f"  🎉 Estado de Onboarding {action}")
    print("=" * 60)
    print(f"  • Usuario:    {user['username']}")
    print(f"  • Email:      {user['email']}")
    print(f"  • ID:         {user['id']}")
    print(f"  • Onboarding: {'0 (False - Verá el asistente)' if not completed else '1 (True - Acceso directo)'}")

    conn.close()

    print("\n💡 Próximos pasos:")
    if not completed:
        print("  1. Abre tu navegador en: http://localhost:5173/")
        print("  2. Recarga la página (F5 o Ctrl+R).")
        print("  3. El sistema te llevará directamente a /onboarding para probar el flujo completo.\n")
    else:
        print("  1. Abre tu navegador en: http://localhost:5173/")
        print("  2. Entrarás directamente a la cartera de inmuebles.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Reinicia el estado de onboarding de un usuario en Arrendis."
    )
    parser.add_argument(
        "identifier",
        nargs="?",
        default="CarlosCanoAdmin",
        help="Username o email del usuario (por defecto: 'CarlosCanoAdmin')",
    )
    parser.add_argument(
        "--completed",
        action="store_true",
        help="Marcar como completado (1) en vez de reiniciar a pendiente (0)",
    )

    args = parser.parse_args()
    reset_onboarding(
        identifier=args.identifier,
        completed=args.completed,
    )


if __name__ == "__main__":
    main()
