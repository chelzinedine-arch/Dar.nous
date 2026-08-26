import os

import psycopg2
from psycopg2.extras import RealDictCursor

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)

from dotenv import load_dotenv

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# =========================================================
# CONFIG
# =========================================================

load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "dar_nous_secret_key"
)


# =========================================================
# DATABASE
# =========================================================

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


# =========================================================
# DATABASE INIT
# =========================================================

def init_db():

    conn = get_db()
    cur = conn.cursor()

    # -----------------------------------------------------
    # USERS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # PROPERTIES
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # INDEXES
    # -----------------------------------------------------

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


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html",
        username=session.get("username")
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":

        return render_template(
            "register.html",
            message=""
        )

    username = request.form.get(
        "username",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )

    first_name = request.form.get(
        "first_name",
        ""
    ).strip()

    last_name = request.form.get(
        "last_name",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not username or not email or not password:

        return render_template(
            "register.html",
            message="Veuillez remplir tous les champs obligatoires."
        )

    if len(username) < 3:

        return render_template(
            "register.html",
            message="Le nom d'utilisateur doit contenir au moins 3 caractères."
        )

    if len(password) < 6:

        return render_template(
            "register.html",
            message="Le mot de passe doit contenir au moins 6 caractères."
        )

    # -----------------------------------------------------
    # HASH PASSWORD
    # -----------------------------------------------------

    password_hash = generate_password_hash(
        password
    )

    conn = None

    try:

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO users (
                username,
                email,
                password_hash,
                first_name,
                last_name,
                phone
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id
        """, (
            username,
            email,
            password_hash,
            first_name or None,
            last_name or None,
            phone or None
        ))

        user = cur.fetchone()

        conn.commit()

        cur.close()
        conn.close()

        # Login مباشرة بعد التسجيل
        session.clear()

        session["user_id"] = user["id"]
        session["username"] = username

        return redirect(
            url_for("home")
        )

    except psycopg2.errors.UniqueViolation:

        if conn:

            conn.rollback()
            conn.close()

        return render_template(
            "register.html",
            message="Username ou email déjà utilisé."
        )

    except Exception as e:

        if conn:

            conn.rollback()
            conn.close()

        return render_template(
            "register.html",
            message=f"Erreur: {e}"
        )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":

        return render_template(
            "login.html",
            message=""
        )

    username = request.form.get(
        "username",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )

    if not username or not password:

        return render_template(
            "login.html",
            message="Veuillez remplir tous les champs."
        )

    conn = None

    try:

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                username,
                email,
                password_hash,
                first_name,
                last_name
            FROM users
            WHERE username = %s
        """, (
            username,
        ))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if not user:

            return render_template(
                "login.html",
                message="Nom d'utilisateur ou mot de passe incorrect."
            )

        if not check_password_hash(
            user["password_hash"],
            password
        ):

            return render_template(
                "login.html",
                message="Nom d'utilisateur ou mot de passe incorrect."
            )

        session.clear()

        session["user_id"] = user["id"]

        session["username"] = user["username"]

        return redirect(
            url_for("home")
        )

    except Exception as e:

        if conn:

            conn.close()

        return render_template(
            "login.html",
            message=f"Erreur: {e}"
        )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile")
def profile():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = None

    try:

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                username,
                email,
                first_name,
                last_name,
                phone,
                profile_image,
                is_verified,
                created_at
            FROM users
            WHERE id = %s
        """, (
            session["user_id"],
        ))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if not user:

            session.clear()

            return redirect(
                url_for("login")
            )

        return render_template(
            "profile.html",
            user=user,
            message=""
        )

    except Exception as e:

        if conn:

            conn.close()

        return render_template(
            "profile.html",
            user=None,
            message=f"Erreur: {e}"
        )


# =========================================================
# UPDATE PROFILE
# =========================================================

@app.route("/profile/update", methods=["POST"])
def update_profile():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    first_name = request.form.get(
        "first_name",
        ""
    ).strip()

    last_name = request.form.get(
        "last_name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    if not email:

        return redirect(
            url_for("profile")
        )

    conn = None

    try:

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            UPDATE users

            SET
                first_name = %s,
                last_name = %s,
                email = %s,
                phone = %s,
                updated_at = CURRENT_TIMESTAMP

            WHERE id = %s
        """, (
            first_name or None,
            last_name or None,
            email,
            phone or None,
            session["user_id"]
        ))

        conn.commit()

        cur.close()
        conn.close()

        return redirect(
            url_for("profile")
        )

    except psycopg2.errors.UniqueViolation:

        if conn:

            conn.rollback()
            conn.close()

        return render_template(
            "profile.html",
            user={
                "username": session.get("username"),
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
                "is_verified": False
            },
            message="Cet email est déjà utilisé."
        )

    except Exception as e:

        if conn:

            conn.rollback()
            conn.close()

        return render_template(
            "profile.html",
            user={
                "username": session.get("username"),
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
                "is_verified": False
            },
            message=f"Erreur: {e}"
        )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = None

    try:

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                title,
                description,
                property_type,
                price,
                city,
                district,
                address,
                latitude,
                longitude,
                surface,
                bedrooms,
                bathrooms,
                furnished,
                parking,
                elevator,
                air_conditioning,
                status,
                created_at,
                updated_at
            FROM properties
            WHERE owner_id = %s
            ORDER BY created_at DESC
        """, (
            session["user_id"],
        ))

        properties = cur.fetchall()

        cur.close()
        conn.close()

        return render_template(
            "dashboard.html",
            properties=properties,
            message=""
        )

    except Exception as e:

        if conn:

            conn.close()

        return render_template(
            "dashboard.html",
            properties=[],
            message=f"Erreur: {e}"
        )


# =========================================================
# ADD PROPERTY
# =========================================================

@app.route("/add_property", methods=["GET", "POST"])
def add_property():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if request.method == "GET":

        return render_template(
            "add_property.html",
            message=""
        )

    # -----------------------------------------------------
    # FORM DATA
    # -----------------------------------------------------

    title = request.form.get(
        "title",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    property_type = request.form.get(
        "property_type",
        ""
    ).strip()

    price = request.form.get(
        "price",
        ""
    ).strip()

    city = request.form.get(
        "city",
        ""
    ).strip()

    district = request.form.get(
        "district",
        ""
    ).strip()

    address = request.form.get(
        "address",
        ""
    ).strip()

    surface = request.form.get(
        "surface",
        ""
    ).strip()

    bedrooms = request.form.get(
        "bedrooms",
        "0"
    ).strip()

    bathrooms = request.form.get(
        "bathrooms",
        "0"
    ).strip()

    latitude = request.form.get(
        "latitude",
        ""
    ).strip()

    longitude = request.form.get(
        "longitude",
        ""
    ).strip()

    furnished = (
        request.form.get("furnished") == "on"
    )

    parking = (
        request.form.get("parking") == "on"
    )

    elevator = (
        request.form.get("elevator") == "on"
    )

    air_conditioning = (
        request.form.get("air_conditioning") == "on"
    )


    # -----------------------------------------------------
    # REQUIRED FIELDS
    # -----------------------------------------------------

    if (
        not title
        or not property_type
        or not city
        or not price
    ):

        return render_template(
            "add_property.html",
            message="Titre, type, ville et prix sont obligatoires."
        )


    # -----------------------------------------------------
    # NUMERIC VALUES
    # -----------------------------------------------------

    try:

        price_value = float(price)

        surface_value = (
            float(surface)
            if surface
            else None
        )

        bedrooms_value = int(
            bedrooms or 0
        )

        bathrooms_value = int(
            bathrooms or 0
        )

        latitude_value = (
            float(latitude)
            if latitude
            else None
        )

        longitude_value = (
            float(longitude)
            if longitude
            else None
        )

    except ValueError:

        return render_template(
            "add_property.html",
            message="Vérifiez les valeurs numériques."
        )


    # -----------------------------------------------------
    # EXTRA VALIDATION
    # -----------------------------------------------------

    if price_value < 0:

        return render_template(
            "add_property.html",
            message="Le prix doit être positif."
        )

    if bedrooms_value < 0:

        return render_template(
            "add_property.html",
            message="Le nombre de chambres est invalide."
        )

    if bathrooms_value < 0:

        return render_template(
            "add_property.html",
            message="Le nombre de salles de bain est invalide."
        )


    conn = None

    try:

        conn = get_db()
        cur = conn.cursor()

        # -------------------------------------------------
        # INSERT PROPERTY
        # -------------------------------------------------

        cur.execute("""
            INSERT INTO properties (
                owner_id,
                title,
                description,
                property_type,
                price,
                city,
                district,
                address,
                latitude,
                longitude,
                surface,
                bedrooms,
                bathrooms,
                furnished,
                parking,
                elevator,
                air_conditioning,
                status
            )

            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'active'
            )

            RETURNING id
        """, (
            session["user_id"],
            title,
            description or None,
            property_type,
            price_value,
            city,
            district or None,
            address or None,
            latitude_value,
            longitude_value,
            surface_value,
            bedrooms_value,
            bathrooms_value,
            furnished,
            parking,
            elevator,
            air_conditioning
        ))

        new_property = cur.fetchone()

        conn.commit()

        cur.close()
        conn.close()

        # مهم:
        # كنرجعو مباشرة للـdashboard
        # باش الإعلان الجديد يبان فيه.
        return redirect(
            url_for("dashboard")
        )


    except Exception as e:

        if conn:

            conn.rollback()
            conn.close()

        return render_template(
            "add_property.html",
            message=f"Erreur lors de la création de l'annonce: {e}"
        )


# =========================================================
# PROPERTY DETAILS
# =========================================================

@app.route("/property/<int:property_id>")
def property_details(property_id):

    conn = None

    try:

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT

                p.id,
                p.title,
                p.description,
                p.property_type,
                p.price,
                p.city,
                p.district,
                p.address,
                p.latitude,
                p.longitude,
                p.surface,
                p.bedrooms,
                p.bathrooms,
                p.furnished,
                p.parking,
                p.elevator,
                p.air_conditioning,
                p.status,
                p.created_at,

                u.id AS owner_id,
                u.username AS owner_username,
                u.first_name AS owner_first_name,
                u.last_name AS owner_last_name,
                u.phone AS owner_phone,
                u.profile_image AS owner_profile_image,
                u.is_verified AS owner_verified

            FROM properties p

            INNER JOIN users u
                ON p.owner_id = u.id

            WHERE p.id = %s
        """, (
            property_id,
        ))

        property_data = cur.fetchone()

        cur.close()
        conn.close()

        if not property_data:

            return "Property not found", 404

        return render_template(
            "property.html",
            property=property_data
        )

    except Exception as e:

        if conn:

            conn.close()

        return f"Database error: {e}", 500


# =========================================================
# API - CURRENT USER
# =========================================================

@app.route("/api/me")
def current_user():

    if "user_id" not in session:

        return jsonify({
            "logged_in": False
        })


    conn = None

    try:

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                username,
                email,
                first_name,
                last_name,
                phone,
                profile_image,
                is_verified,
                created_at
            FROM users
            WHERE id = %s
        """, (
            session["user_id"],
        ))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if not user:

            session.clear()

            return jsonify({
                "logged_in": False
            })

        return jsonify({
            "logged_in": True,
            "user": user
        })

    except Exception as e:

        if conn:

            conn.close()

        return jsonify({
            "logged_in": False,
            "error": str(e)
        }), 500


# =========================================================
# DATABASE TEST
# =========================================================

@app.route("/api/db-test")
def db_test():

    try:

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                (SELECT COUNT(*) FROM users)
                    AS users_count,

                (SELECT COUNT(*) FROM properties)
                    AS properties_count
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


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    try:

        init_db()

        print("===================================")
        print("Dar.nous Database: CONNECTED")
        print("Users table: READY")
        print("Properties table: READY")
        print("===================================")

    except Exception as e:

        print("===================================")
        print("DATABASE ERROR")
        print(e)
        print("===================================")

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )