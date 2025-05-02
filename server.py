from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from threading import Lock
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()  # Charge les variables depuis .env

app = Flask(__name__)
CORS(app)
db_lock = Lock()

# Connexion à MongoDB
def get_db_connection():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    db = client.game_db  # Utilisation de la base de données game_db
    return db

# Création ou mise à jour du schéma
def init_db():
    db = get_db_connection()
    players = db.players
    if "players" not in db.list_collection_names():
        players.create_index("pseudo", unique=True)

@app.route('/')
def home():
    db = get_db_connection()
    players = db.players.find()
    return render_template('index.html', joueurs=players)

@app.route('/api/economie')
def economie():
    db = get_db_connection()
    players = db.players.find({}, {"_id": 0, "pseudo": 1, "argent": 1, "avatar": 1})
    return jsonify([player for player in players])

@app.route('/api/ajouter_joueur', methods=['POST'])
def ajouter_joueur():
    data = request.get_json()
    pseudo = data['pseudo']
    db = get_db_connection()
    players = db.players
    if players.find_one({"pseudo": pseudo}):
        return jsonify({"status": "error", "message": "Le joueur existe déjà!"}), 400

    players.insert_one({"pseudo": pseudo, "argent": 0})
    return jsonify({"status": "success", "message": f"Joueur {pseudo} ajouté avec succès!"})

@app.route('/api/ajouter_argent', methods=['POST'])
def ajouter_argent():
    data = request.json
    pseudo = data.get("pseudo")
    montant = data.get("montant")

    if not pseudo or montant is None:
        return jsonify({"error": "Champs manquants"}), 400

    db = get_db_connection()
    players = db.players
    player = players.find_one({"pseudo": pseudo})

    if player:
        players.update_one({"pseudo": pseudo}, {"$inc": {"argent": montant}})
    else:
        players.insert_one({"pseudo": pseudo, "argent": montant})

    return jsonify({"message": f"{montant} pièces ajoutées à {pseudo}."})

@app.route('/api/solde/<pseudo>')
def get_solde(pseudo):
    db = get_db_connection()
    players = db.players
    player = players.find_one({"pseudo": pseudo})

    if player:
        return jsonify({"pseudo": pseudo, "solde": player['argent']})
    else:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

@app.route('/api/supprimer_joueur', methods=['POST'])
def supprimer_joueur():
    data = request.get_json()
    pseudo = data.get('pseudo')

    if not pseudo:
        return jsonify({"error": "Pseudo manquant"}), 400

    db = get_db_connection()
    players = db.players
    players.delete_one({"pseudo": pseudo})

    return jsonify({"message": f"Le joueur {pseudo} a été supprimé avec succès."})

@app.route('/api/creer_compte', methods=['POST'])
def creer_compte():
    data = request.get_json()
    pseudo = data.get('pseudo')

    if not pseudo:
        return jsonify({"error": "Pseudo manquant"}), 400

    db = get_db_connection()
    players = db.players
    if players.find_one({"pseudo": pseudo}):
        return jsonify({"message": f"Le compte pour {pseudo} existe déjà."})

    players.insert_one({"pseudo": pseudo, "argent": 100})
    return jsonify({"message": f"Compte créé pour {pseudo} avec 100 pièces."})

@app.route('/api/set_avatar', methods=['POST'])
def set_avatar():
    data = request.get_json()
    pseudo = data.get('pseudo').lower()
    avatar_url = data.get('avatar_url')

    with db_lock:
        db = get_db_connection()
        players = db.players
        players.update_one({"pseudo": pseudo}, {"$set": {"avatar": avatar_url}})

    return jsonify({"status": "success", "message": "Avatar mis à jour."})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)
