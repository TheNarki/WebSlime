from flask import Flask, jsonify, request
import sqlite3
from flask import Flask, render_template

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('game.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            pseudo TEXT UNIQUE,
            argent INTEGER
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

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

@app.route('/api/ajouter_argent', methods=['POST'])
def ajouter_argent():
    try:
        data = request.get_json()
        pseudo = data['pseudo']
        montant = data['montant']
        conn = get_db_connection()
        joueur = conn.execute('SELECT * FROM players WHERE pseudo = ?', (pseudo,)).fetchone()
        if joueur:
            nouveau_solde = joueur['argent'] + montant
            conn.execute('UPDATE players SET argent = ? WHERE pseudo = ?', (nouveau_solde, pseudo))
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "message": f"{montant} pièces ajoutées à {pseudo}."}), 200
        else:
            conn.close()
            return jsonify({"status": "error", "message": "Joueur non trouvé!"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/api/solde/<pseudo>', methods=['GET'])
def get_solde(pseudo):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT solde FROM economie WHERE pseudo = ?", (pseudo,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return jsonify({"pseudo": pseudo, "solde": result['solde']})
    else:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

if __name__ == '__main__':  
    init_db()
    app.run(host='0.0.0.0', port=10000)  # le port peut être ignoré par Render
