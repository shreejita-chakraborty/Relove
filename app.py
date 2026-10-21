import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, session, redirect, url_for,abort
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "relove-prototype-secret-key-change-later"
DATABASE = "relove.db"

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db
def create_table():
    with get_db() as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                shop_name TEXT,
                shop_category TEXT,
                gst_number TEXT,
                shop_address TEXT,
                phone TEXT
            )
            """)
        cursor = db.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [row["name"] for row in cursor.fetchall()]

        if "shop_category" not in columns:
            db.execute(
                "ALTER TABLE users ADD COLUMN shop_category TEXT"
            )
        db.commit()    
        db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                size TEXT,
                category TEXT NOT NULL,
                description TEXT,
                genre TEXT,
                price REAL NOT NULL,
                image TEXT,
                stock INTEGER DEFAULT 1,
                FOREIGN KEY (shop_id) REFERENCES users(id)
            )
        """)
        cursor.execute("PRAGMA table_info(products)")
        product_columns = [row["name"] for row in cursor.fetchall()]
        if "clothing_type" not in product_columns:
            cursor.execute("ALTER TABLE products ADD COLUMN clothing_type TEXT")
        if "genre" not in product_columns:
            cursor.execute("ALTER TABLE products ADD COLUMN genre TEXT")
        if "size" not in product_columns:
            cursor.execute("ALTER TABLE products ADD COLUMN size TEXT")
        db.commit()
@app.route("/")
@app.route("/index")
@app.route("/index.html")
@app.route("/")
def home():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, shop_name, shop_address, shop_category
        FROM users
        WHERE role = 'shop'
    """)
    shops = cursor.fetchall()
    conn.close()
    return render_template("index.html", shops=shops)
@app.route("/books")
@app.route("/books.html")
def books():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, shop_name, shop_address
        FROM users
        WHERE role = 'shop' AND shop_category = 'books'
    """)
    shops = cursor.fetchall()
    cursor.execute("""
        SELECT products.*, users.shop_name, users.shop_address
        FROM products
        JOIN users ON products.shop_id = users.id
        WHERE products.category = 'books'
          AND users.role = 'shop'
        ORDER BY products.id DESC
    """)
    products = cursor.fetchall()

    conn.close()

    return render_template(
        "books.html",
        shops=shops,
        products=products
    )

@app.route("/clothes")
@app.route("/clothes.html")
def clothes():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, shop_name, shop_address
        FROM users
        WHERE role = 'shop' AND shop_category = 'clothes'
    """)
    shops = cursor.fetchall()
    cursor.execute("""
        SELECT products.*, users.shop_name, users.shop_address
        FROM products
        JOIN users ON products.shop_id = users.id
        WHERE products.category = 'clothes'
          AND users.role = 'shop'
        ORDER BY products.id DESC
    """)
    products = cursor.fetchall()
    conn.close()
    return render_template(
        "clothes.html",
        shops=shops,
        products=products
    )
@app.route("/aboutus")
@app.route("/aboutus.html")
def about():
    return render_template("aboutus.html")

@app.route("/login")
@app.route("/login.html")
def login():
    return render_template("login.html")

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    full_name = data.get("fullName", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "")
    shop_category = (
    data.get("shopCategory")
    if role == "shop"
    else None
    )

    if not full_name or not email or len(password) < 8:
        return jsonify(
            success=False,
            message="Enter your name, a valid email, and a password of at least 8 characters."
        ), 400

    if role not in ("customer", "shop"):
        return jsonify(success=False, message="Invalid account type."), 400

    shop_name = data.get("shopName", "").strip()
    gst_number = data.get("gstNumber", "").strip().upper()
    shop_address = data.get("shopAddress", "").strip()
    phone = data.get("phone", "").strip()
    shop_category = (
    data.get("shopCategory")
    if role == "shop"
    else None
    )

    if role == "shop" and not all([shop_name, shop_address, phone]):
        return jsonify(
            success=False,
            message="Please complete your shop details."
        ), 400
    
    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO users (
                    full_name, email, password, role,
                    shop_name, gst_number, shop_address, phone,
                    shop_category
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                full_name, email, generate_password_hash(password), role,
                shop_name, gst_number, shop_address, phone,
                shop_category
            ))

        return jsonify(
            success=True,
            message="Account created! You can now log in."
        )

    except sqlite3.IntegrityError:
        return jsonify(
            success=False,
            message="An account with this email already exists."
        ), 409

@app.route("/api/login", methods=["POST"])
def login_user():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "")

    with get_db() as db:
        user = db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

    if (
        user is None
        or role not in ("customer", "shop")
        or user["role"] != role
        or not check_password_hash(user["password"], password)
    ):
        return jsonify(
            success=False,
            message="Incorrect email, password, or account type."
        ), 401

    session["user_id"] = user["id"]
    session["user_role"] = user["role"]
    session["user_name"] = user["full_name"]

    return jsonify(
        success=True,
        message="Login successful! Welcome back.",
        redirect="/"
    )

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("home"))
@app.route("/store/<int:shop_id>")
def view_store(shop_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, shop_name, shop_address FROM users WHERE id = ? AND role = 'shop'",
        (shop_id,)
    )
    shop = cursor.fetchone()

    if shop is None:
        conn.close()
        abort(404)

    cursor.execute(
        "SELECT * FROM products WHERE shop_id = ?",
        (shop_id,)
    )
    products = cursor.fetchall()
    conn.close()

    return render_template(
        "store.html",
        shop=shop,
        products=products
    )
@app.route("/add-product", methods=["GET", "POST"])
def add_product():
    if session.get("user_role") != "shop":
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        genre = request.form.get("genre", "").strip() or None
        size = request.form.get("size", "").strip() or None
        clothing_type = request.form.get("clothing_type", "").strip() or None
        description = request.form.get("description", "").strip()
        price = request.form.get("price", type=float)
        stock = request.form.get("stock", type=int)

        if not name or category not in ("books", "clothes"):
            return "Invalid product details", 400

        if price is None or price < 0 or stock is None or stock < 1:
            return "Invalid price or quantity", 400
        if category == "clothes" and not clothing_type:
            conn.close()
            return "Please select a clothing type.", 400
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT shop_category FROM users WHERE id = ? AND role = 'shop'",
            (session["user_id"],)
        )
        shop = cursor.fetchone()

        if shop is None or shop["shop_category"] != category:
            conn.close()
            return "Product category must match your shop category.", 400
        if category == "books" and not genre:
            conn.close()
            return "Please select a genre for the book.", 
        if category == "clothes" and not size:
            conn.close()
            return "Please select a clothing size.", 400
        image_file = request.files.get("image")
        if not image_file or not image_file.filename:
            conn.close()
            return "Please upload a product image.", 400
        filename = secure_filename(image_file.filename)
        if not filename:
            conn.close()
            return "Invalid image filename.", 400

        image_name = f"{session['user_id']}_{filename}"
        upload_folder = os.path.join(app.static_folder, "images", "products")
        os.makedirs(upload_folder, exist_ok=True)

        image_file.save(os.path.join(upload_folder, image_name))
        print("UPLOAD FOLDER:", upload_folder)
        print("SAVED IMAGE:", os.path.join(upload_folder, image_name))
        print("FILE EXISTS:", os.path.exists(os.path.join(upload_folder, image_name)))

        try:
            cursor.execute("""
                    INSERT INTO products
                    (shop_id, name, category, genre, clothing_type,
                    description, price, image, stock)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session["user_id"], name, category, genre, clothing_type,
                    description, price, image_name, stock
                ))
            conn.commit()
        except Exception:
            conn.close()
            raise
        else:
            conn.close()

        return redirect(url_for(
            "view_store", shop_id=session["user_id"]
        ))

    return render_template("addproduct.html")
@app.route("/add-to-cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    with get_db() as db:
        product = db.execute(
            "SELECT id, stock FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()

    if product is None:
        abort(404)

    if product["stock"] < 1:
        return "This product is out of stock.", 400

    cart = session.get("cart", {})
    product_key = str(product_id)

    current_quantity = cart.get(product_key, 0)

    if current_quantity >= product["stock"]:
        return "You have added all available stock.", 400

    cart[product_key] = current_quantity + 1
    session["cart"] = cart

    return redirect(request.referrer or url_for("home"))
if   __name__ == "__main__":
    create_table()
    app.run(debug=True)