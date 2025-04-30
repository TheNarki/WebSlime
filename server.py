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
    data = request.json
    pseudo = data.get("pseudo")
    montant = data.get("montant")

    if not pseudo or montant is None:
        return jsonify({"error": "Champs manquants"}), 400

    conn = sqlite3.connect('economie.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM economie WHERE pseudo = ?", (pseudo,))
    row = cursor.fetchone()

    if row:
        cursor.execute("UPDATE economie SET argent = argent + ? WHERE pseudo = ?", (montant, pseudo))
    else:
        cursor.execute("INSERT INTO economie (pseudo, argent) VALUES (?, ?)", (pseudo, montant))

    conn.commit()
    conn.close()

    return jsonify({"message": f"{montant} pièces ajoutées à {pseudo}."})
    
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
    
@app.route('/api/supprimer_joueur', methods=['POST'])
def supprimer_joueur():
    data = request.get_json()
    pseudo = data.get('pseudo')

    # Supprimer le joueur de la base de données
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM joueurs WHERE pseudo = ?", (pseudo,))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Le joueur {pseudo} a été supprimé avec succès."})

if __name__ == '__main__':  
    init_db()
    app.run(host='0.0.0.0', port=10000)  # le port peut être ignoré par Render
