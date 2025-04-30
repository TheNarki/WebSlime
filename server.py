from flask import Flask, jsonify, request
import sqlite3
from flask import render_template
from flask_cors import CORS

app = Flask(__name__)

# Appliquer CORS à l'application Flask
CORS(app)

# Connexion à la base de données
def get_db_connection():
    conn = sqlite3.connect('game.db')
    conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
    return conn

# Initialisation de la base de données
def init_db():
    conn = get_db_connection()
    conn.execute(''' 
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            pseudo TEXT UNIQUE,
            argent INTEGER DEFAULT 0
        );
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

# Ajouter un joueur à la base de données
@app.route('/api/ajouter_joueur', methods=['POST'])
def ajouter_joueur():
    try:
        data = request.get_json()
        pseudo = data['pseudo']
        conn = get_db_connection()
        conn.execute('INSERT INTO players (pseudo, argent) VALUES (?, ?)', (pseudo, 0))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"Joueur {pseudo} ajouté avec succès!"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Le joueur existe déjà!"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/economie')
def economie():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pseudo, argent FROM players")
    rows = cursor.fetchall()
    conn.close()

    # Si des joueurs existent dans la base de données
    if rows:
        players = [{"pseudo": row["pseudo"], "argent": row["argent"]} for row in rows]
        return jsonify(players)
    else:
        return jsonify({"error": "Aucun joueur trouvé"}), 404
# Ajouter de l'argent à un joueur
@app.route('/api/ajouter_argent', methods=['POST'])
def ajouter_argent():
    data = request.json
    pseudo = data.get("pseudo")
    montant = data.get("montant")

    if not pseudo or montant is None:
        return jsonify({"error": "Champs manquants"}), 400

    # Connexion à la base de données
    conn = get_db_connection()
    cursor = conn.cursor()

    # Vérifier si le joueur existe
    cursor.execute("SELECT argent FROM players WHERE pseudo = ?", (pseudo,))
    joueur = cursor.fetchone()

    if joueur:
        # Ajouter de l'argent
        cursor.execute("UPDATE players SET argent = argent + ? WHERE pseudo = ?", (montant, pseudo))
    else:
        # Si le joueur n'existe pas, on le crée avec l'argent
        cursor.execute("INSERT INTO players (pseudo, argent) VALUES (?, ?)", (pseudo, montant))

    conn.commit()
    conn.close()

    return jsonify({"message": f"{montant} pièces ajoutées à {pseudo}."})

# Récupérer le solde d'un joueur
@app.route('/api/solde/<pseudo>', methods=['GET'])
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

# Supprimer un joueur
@app.route('/api/supprimer_joueur', methods=['POST'])
def supprimer_joueur():
    data = request.get_json()
    pseudo = data.get('pseudo')

    if not pseudo:
        return jsonify({"error": "Pseudo manquant"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM players WHERE pseudo = ?", (pseudo,))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Le joueur {pseudo} a été supprimé avec succès."})

if __name__ == '__main__':  
    init_db()  # Initialiser la base de données au démarrage
    app.run(host='0.0.0.0', port=10000)  # Le port peut être ignoré par Render
