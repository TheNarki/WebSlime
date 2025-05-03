from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from threading import Lock

# Define a threading lock
db_lock = Lock()
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
import psycopg2
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_cors import CORS
import os

# Ajoute ce pour utiliser les sessions


load_dotenv()

db_user = os.getenv("DB_USER")
db_password = quote_plus(os.getenv("DB_PASSWORD"))
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}.oregon-postgres.render.com:{db_port}/{db_name}"

# Connexion SQLAlchemy
engine = create_engine(DATABASE_URL)

# Connexion psycopg2 pour test
try:
    conn = psycopg2.connect(DATABASE_URL)
    print("Connexion réussie à la base de données")
    conn.close()
except Exception as e:
    print(f"Erreur de connexion : {e}")

app = Flask(__name__)
app = Flask(__name__)
CORS(app)

# Ajoute ce pour utiliser les sessions
app.secret_key = os.getenv("SECRET_KEY", "admin")

def init_db():
    with engine.connect() as conn:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS players (
                id SERIAL PRIMARY KEY,
                pseudo TEXT UNIQUE NOT NULL,
                argent INTEGER DEFAULT 0,
                avatar TEXT
            );
        '''))
        conn.commit()

@app.route('/')
def home():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT pseudo, argent, avatar FROM players"))
        players = result.fetchall()
        return render_template('index.html', joueurs=players)

@app.route('/api/economie')
def economie():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT pseudo, argent, avatar FROM players"))
        players = [dict(row._mapping) for row in result]
        return jsonify(players)

@app.route('/api/ajouter_joueur', methods=['POST'])
def ajouter_joueur():
    data = request.get_json()
    pseudo = data['pseudo']
    try:
        with engine.connect() as conn:
            conn.execute(text("INSERT INTO players (pseudo, argent) VALUES (:pseudo, 0)"), {"pseudo": pseudo})
            conn.commit()
        return jsonify({"status": "success", "message": f"Joueur {pseudo} ajouté avec succès!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/ajouter_argent', methods=['POST'])
def ajouter_argent():
    data = request.json
    pseudo = data.get("pseudo")
    montant = data.get("montant")
    if not pseudo or montant is None:
        return jsonify({"error": "Champs manquants"}), 400

    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM players WHERE pseudo = :pseudo"), {"pseudo": pseudo}).fetchone()
        if result:
            conn.execute(text("UPDATE players SET argent = argent + :montant WHERE pseudo = :pseudo"), {"pseudo": pseudo, "montant": montant})
        else:
            conn.execute(text("INSERT INTO players (pseudo, argent) VALUES (:pseudo, :montant)"), {"pseudo": pseudo, "montant": montant})
        conn.commit()
    return jsonify({"message": f"{montant} pièces ajoutées à {pseudo}."})

@app.route('/api/solde/<pseudo>')
def get_solde(pseudo):
    with engine.connect() as conn:
        player = conn.execute(text("SELECT argent FROM players WHERE pseudo = :pseudo"), {"pseudo": pseudo}).fetchone()
        if player:
            return jsonify({"pseudo": pseudo, "solde": player[0]})
        else:
            return jsonify({"error": "Utilisateur non trouvé"}), 404

@app.route('/api/supprimer_joueur', methods=['POST'])
def supprimer_joueur():
    data = request.get_json()
    pseudo = data.get('pseudo')
    if not pseudo:
        return jsonify({"error": "Pseudo manquant"}), 400
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM players WHERE pseudo = :pseudo"), {"pseudo": pseudo})
        conn.commit()
    return jsonify({"message": f"Le joueur {pseudo} a été supprimé avec succès."})

@app.route('/api/creer_compte', methods=['POST'])
def creer_compte():
    data = request.get_json()
    pseudo = data.get('pseudo')
    if not pseudo:
        return jsonify({"error": "Pseudo manquant"}), 400
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 FROM players WHERE pseudo = :pseudo"), {"pseudo": pseudo}).fetchone()
        if result:
            return jsonify({"message": f"Le compte pour {pseudo} existe déjà."})
        conn.execute(text("INSERT INTO players (pseudo, argent) VALUES (:pseudo, 100)"), {"pseudo": pseudo})
        conn.commit()
    return jsonify({"message": f"Compte créé pour {pseudo} avec 100 pièces."})

@app.route('/api/set_avatar', methods=['POST'])
def set_avatar():
    data = request.get_json()
    pseudo = data.get('pseudo').lower()
    avatar_url = data.get('avatar_url')
    with db_lock:
        with engine.connect() as conn:
            conn.execute(text("UPDATE players SET avatar = :avatar WHERE pseudo = :pseudo"), {"avatar": avatar_url, "pseudo": pseudo})
            conn.commit()
    return jsonify({"status": "success", "message": "Avatar mis à jour."})

@app.route('/admin')
def admin():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    with engine.connect() as conn:
        joueurs = conn.execute(text("SELECT pseudo, argent, avatar FROM players")).fetchall()
    return render_template("admin.html", joueurs=joueurs)

@app.route('/admin/ajouter_argent', methods=["POST"])
def admin_ajouter_argent():
    pseudo = request.form.get("pseudo")
    montant = int(request.form.get("montant", 0))
    with engine.connect() as conn:
        conn.execute(text("UPDATE players SET argent = argent + :montant WHERE pseudo = :pseudo"), {"pseudo": pseudo, "montant": montant})
        conn.commit()
    return redirect(url_for("admin"))

@app.route('/admin/set_avatar', methods=["POST"])
def admin_set_avatar():
    pseudo = request.form.get("pseudo").lower()
    avatar_url = request.form.get("avatar_url")
    with engine.connect() as conn:
        conn.execute(text("UPDATE players SET avatar = :avatar WHERE pseudo = :pseudo"), {"pseudo": pseudo, "avatar": avatar_url})
        conn.commit()
    return redirect(url_for("admin"))

@app.route('/admin/supprimer', methods=["POST"])
def admin_supprimer():
    pseudo = request.form.get("pseudo")
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM players WHERE pseudo = :pseudo"), {"pseudo": pseudo})
        conn.commit()
    return redirect(url_for("admin"))


@app.route('/admin/update', methods=['POST'])
def update_argent():
    pseudo = request.form.get('pseudo')
    argent = request.form.get('argent')
    if not pseudo or not argent:
        return "Champs requis manquants", 400

    try:
        argent = int(argent)
        with engine.connect() as conn:
            conn.execute(text("UPDATE players SET argent = :argent WHERE pseudo = :pseudo"),
                         {"argent": argent, "pseudo": pseudo})
            conn.commit()
        return "Argent mis à jour avec succès. <a href='/admin'>Retour</a>"
    except Exception as e:
        return f"Erreur : {e}", 500
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == os.getenv("ADMIN_PASSWORD"):
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return "Mot de passe incorrect", 403
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)
