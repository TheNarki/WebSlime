from flask import Flask, jsonify, request, render_template
import sqlite3
from flask_cors import CORS
from threading import Lock

app = Flask(__name__)
CORS(app)
db_lock = Lock()

# Connexion à la base de données
def get_db_connection():
    conn = sqlite3.connect('game.db')
    conn.row_factory = sqlite3.Row
    return conn

# Création ou mise à jour du schéma
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Crée la table si elle n'existe pas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            pseudo TEXT PRIMARY KEY,
            argent INTEGER DEFAULT 0
        )
    ''')
    conn.commit()

    # Récupère les colonnes existantes
    cursor.execute("PRAGMA table_info(players)")
    existing_columns = [col[1] for col in cursor.fetchall()]

    if "id" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN id TEXT")
        print("✅ Colonne 'id' ajoutée.")

    if "avatar" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN avatar TEXT")
        print("✅ Colonne 'avatar' ajoutée.")

    conn.commit()
    conn.close()

@app.route('/')
def home():
    conn = get_db_connection()
    joueurs = conn.execute('SELECT * FROM players').fetchall()
    conn.close()
    return render_template('index.html', joueurs=joueurs)

@app.route('/api/economie')
def economie():
    conn = get_db_connection()
    rows = conn.execute("SELECT pseudo, argent, avatar FROM players").fetchall()
    conn.close()

    players = [
        {
            "pseudo": row["pseudo"],
            "argent": row["argent"],
            "avatar": row["avatar"] or ""  # valeur vide si pas d'avatar
        } for row in rows
    ]
    return jsonify(players)

@app.route('/api/ajouter_joueur', methods=['POST'])
def ajouter_joueur():
    data = request.get_json()
    pseudo = data['pseudo']

    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO players (pseudo, argent) VALUES (?, ?)', (pseudo, 0))
        conn.commit()
        return jsonify({"status": "success", "message": f"Joueur {pseudo} ajouté avec succès!"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Le joueur existe déjà!"}), 400
    finally:
        conn.close()

@app.route('/api/ajouter_argent', methods=['POST'])
def ajouter_argent():
    data = request.json
    pseudo = data.get("pseudo")
    montant = data.get("montant")

    if not pseudo or montant is None:
        return jsonify({"error": "Champs manquants"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT argent FROM players WHERE pseudo = ?", (pseudo,))
    joueur = cursor.fetchone()

    if joueur:
        cursor.execute("UPDATE players SET argent = argent + ? WHERE pseudo = ?", (montant, pseudo))
    else:
        cursor.execute("INSERT INTO players (pseudo, argent) VALUES (?, ?)", (pseudo, montant))

    conn.commit()
    conn.close()
    return jsonify({"message": f"{montant} pièces ajoutées à {pseudo}."})

@app.route('/api/solde/<pseudo>')
def get_solde(pseudo):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT argent FROM players WHERE pseudo = ?", (pseudo,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return jsonify({"pseudo": pseudo, "solde": result['argent']})
    else:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

@app.route('/api/supprimer_joueur', methods=['POST'])
def supprimer_joueur():
    data = request.get_json()
    pseudo = data.get('pseudo')

    if not pseudo:
        return jsonify({"error": "Pseudo manquant"}), 400

    conn = get_db_connection()
    conn.execute("DELETE FROM players WHERE pseudo = ?", (pseudo,))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Le joueur {pseudo} a été supprimé avec succès."})

@app.route('/api/creer_compte', methods=['POST'])
def creer_compte():
    data = request.get_json()
    pseudo = data.get('pseudo')

    if not pseudo:
        return jsonify({"error": "Pseudo manquant"}), 400

    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO players (pseudo, argent) VALUES (?, ?)", (pseudo, 100))
        conn.commit()
        return jsonify({"message": f"Compte créé pour {pseudo} avec 100 pièces."})
    except sqlite3.IntegrityError:
        return jsonify({"message": f"Le compte pour {pseudo} existe déjà."})
    finally:
        conn.close()

@app.route('/api/set_avatar', methods=['POST'])
def set_avatar():
    data = request.get_json()
    pseudo = data.get('pseudo').lower()
    avatar_url = data.get('avatar_url')

    with db_lock:
        conn = get_db_connection()
        conn.execute("UPDATE players SET avatar = ? WHERE pseudo = ?", (avatar_url, pseudo))
        conn.commit()
        conn.close()

    return jsonify({"status": "success", "message": "Avatar mis à jour."})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)
