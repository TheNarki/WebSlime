import sqlite3

def update_schema():
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()

    # Vérifie si la colonne 'id' existe déjà
    cursor.execute("PRAGMA table_info(players);")
    columns = [col[1] for col in cursor.fetchall()]

    if 'id' not in columns:
        cursor.execute("ALTER TABLE players ADD COLUMN id TEXT;")
        print("Colonne 'id' ajoutée.")

    if 'avatar' not in columns:
        cursor.execute("ALTER TABLE players ADD COLUMN avatar TEXT;")
        print("Colonne 'avatar' ajoutée.")

    conn.commit()
    conn.close()
    print("Mise à jour terminée.")

if __name__ == "__main__":
    update_schema()
