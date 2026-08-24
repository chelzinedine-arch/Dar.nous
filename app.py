import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.secret_key = "dar_nous_secret_key"
def get_db():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL n'est pas définie."
        )
    return psycopg2.connect(
        database_url,
        cursor_factory=RealDictCursor
    )
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            phone VARCHAR(30),
            profile_image TEXT,
            is_verified BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id BIGSERIAL PRIMARY KEY,
            owner_id BIGINT NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            property_type VARCHAR(50) NOT NULL,
            price NUMERIC(12,2) NOT NULL,
            city VARCHAR(100) NOT NULL,
            district VARCHAR(150),
            address TEXT,
            latitude NUMERIC(10,7),
            longitude NUMERIC(10,7),
            surface NUMERIC(10,2),
            bedrooms INTEGER NOT NULL DEFAULT 0,
            bathrooms INTEGER NOT NULL DEFAULT 0,
            furnished BOOLEAN NOT NULL DEFAULT FALSE,
            parking BOOLEAN NOT NULL DEFAULT FALSE,
            elevator BOOLEAN NOT NULL DEFAULT FALSE,
            air_conditioning BOOLEAN NOT NULL DEFAULT FALSE,
            status VARCHAR(30) NOT NULL DEFAULT 'active',
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_properties_owner
                FOREIGN KEY (owner_id)
                REFERENCES users(id)
                ON DELETE CASCADE,
            CONSTRAINT properties_price_positive
                CHECK (price >= 0),
            CONSTRAINT properties_surface_positive
                CHECK (
                    surface IS NULL OR surface > 0
                ),
            CONSTRAINT properties_bedrooms_positive
                CHECK (bedrooms >= 0),
            CONSTRAINT properties_bathrooms_positive
                CHECK (bathrooms >= 0),
            CONSTRAINT properties_type_check
                CHECK (
                    property_type IN (
                        'Appartement',
                        'Maison',
                        'Villa',
                        'Studio',
                        'Commerce',
                        'Bureau',
                        'Terrain',
                        'Autre'
                    )
                ),
            CONSTRAINT properties_status_check
                CHECK (
                    status IN (
                        'active',
                        'rented',
                        'pending',
                        'hidden'
                    )
                )
        )
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_properties_owner
        ON properties(owner_id)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_properties_city
        ON properties(city)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_properties_type
        ON properties(property_type)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_properties_price
        ON properties(price)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_properties_status
        ON properties(status)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_properties_created
        ON properties(created_at DESC)
    """)
    conn.commit()
    cur.close()
    conn.close()
@app.route("/")
def home():
    return render_template("index.html")
@app.route("/api/db-test")
def db_test():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                (SELECT COUNT(*) FROM users) AS users_count,
                (SELECT COUNT(*) FROM properties) AS properties_count
        """)
        result = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({
            "success": True,
            "database": "PostgreSQL",
            "users": result["users_count"],
            "properties": result["properties_count"]
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )