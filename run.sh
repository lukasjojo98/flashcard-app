#!/bin/bash

DB_FILE="users.db"
DECKS_DB_FILE="decks.db"

echo "📦 Setup wird gestartet..."

# --- Lade Variablen aus .env ---
if [ ! -f .env ]; then
    echo "❌ .env-Datei nicht gefunden!"
    exit 1
fi

export $(grep -v '^#' .env | xargs)

# --- Prüfe USER_PORT ---
if [ -z "$USER_PORT" ]; then
    echo "❌ USER_PORT ist nicht in der .env-Datei gesetzt."
    exit 1
fi

# --- Prüfe und erstelle users.db ---
if ! command -v sqlite3 &> /dev/null; then
    echo "❌ sqlite3 ist nicht installiert. Bitte installiere es zuerst."
    exit 1
fi

if [ -f "$DB_FILE" ]; then
    echo "✅ $DB_FILE existiert bereits. Keine Aktion notwendig."
else
    echo "📦 Erstelle $DB_FILE mit eingebettetem Schema..."
    sqlite3 "$DB_FILE" <<EOF
CREATE TABLE user (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL);
EOF

    if [ $? -eq 0 ]; then
        echo "✅ $DB_FILE wurde erfolgreich erstellt."
    else
        echo "❌ Fehler beim Erstellen von $DB_FILE."
        exit 1
    fi
fi

# --- Prüfe und erstelle decks.db ---
if ! command -v sqlite3 &> /dev/null; then
    echo "❌ sqlite3 ist nicht installiert. Bitte installiere es zuerst."
    exit 1
fi

if [ -f "$DECKS_DB_FILE" ]; then
    echo "✅ $DECKS_DB_FILE existiert bereits. Keine Aktion notwendig."
else
    echo "📦 Erstelle $DECKS_DB_FILE mit eingebettetem Schema..."
    sqlite3 "$DECKS_DB_FILE" <<EOF
    CREATE TABLE decks (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id int, name TEXT NOT NULL, cards int);
    CREATE TABLE cards (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id int, deck_id int, question TEXT NOT NULL, answer TEXT NOT NULL, four_score int, question_image_path TEXT, answer_image_path TEXT);
EOF

    if [ $? -eq 0 ]; then
        echo "✅ $DECKS_DB_FILE wurde erfolgreich erstellt."
    else
        echo "❌ Fehler beim Erstellen von $DECKS_DB_FILE."
        exit 1
    fi
fi


# --- Docker Image bauen ---
echo "🐳 Baue Docker-Image..."
docker build -t flashcard-app .

# --- Docker Container starten ---
echo "🚀 Starte Container auf Port $USER_PORT ..."
docker run -p $USER_PORT:5000 \
  -v "$(pwd)/users.db:/app/users.db" \
  flashcard-app