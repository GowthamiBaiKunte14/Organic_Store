from flask import Flask, jsonify, render_template, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText


app = Flask(__name__)
app.secret_key = "organic_store_secret"

basedir = os.path.abspath(os.path.dirname(__file__))
db_file = os.path.join(basedir, "store.db")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_file
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

UPLOAD_FOLDER = os.path.join(basedir, "static/uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


db = SQLAlchemy(app)


# ---------------- MODELS ----------------
@app.context_processor
def inject_cart_count():
    cart = session.get("cart", {})
    count = sum(cart.values())
    return dict(cart_count=count)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)

    # base price used as fallback
    price = db.Column(db.Float, nullable=False)

    old_price = db.Column(db.Float, default=0.0)
    discount_pct = db.Column(db.Integer, default=0)
    is_assured = db.Column(db.Boolean, default=True)

    image = db.Column(db.String(200))
    category = db.Column(db.String(100))
    stock = db.Column(db.Integer, default=0)


class ProductVariant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    quantity = db.Column(db.String(50))   # e.g. 250ml, 500ml, 1L
    price = db.Column(db.Float)
    stock = db.Column(db.Integer)

    product = db.relationship("Product", backref="variants")

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50))
    discount = db.Column(db.Integer)  # percentage
    active = db.Column(db.Boolean, default=True)

class Hero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    subtitle = db.Column(db.String(200))
    image = db.Column(db.String(200))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    content = db.Column(db.Text)
    date = db.Column(db.String(50))

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    plan = db.Column(db.String(100))
    date = db.Column(db.String(50))

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    url = db.Column(db.String(300))
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'))

    variant = db.relationship("ProductVariant")

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(150))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    address = db.Column(db.String(200))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50))
    total_price = db.Column(db.Float)
    payment_method = db.Column(db.String(50))
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    customer_address = db.Column(db.Text)
    status = db.Column(db.String(50), default="Pending")

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_name = db.Column(db.String(200))
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(300))


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    user_name = db.Column(db.String(100))
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)

    approved = db.Column(db.Boolean, default=False)
    verified = db.Column(db.Boolean, default=False)

    product = db.relationship('Product', backref='reviews')

with app.app_context():
    db.create_all()

    # create default admin
    admin = Admin.query.first()
    if not admin:
        admin = Admin(
            username="admin",
            password=generate_password_hash("admin123")
        )
        db.session.add(admin)
        db.session.commit()

# ---------------- HELPERS ----------------

def add_recently_viewed(product_id):
    viewed = session.get("recently_viewed", [])

    if product_id in viewed:
        viewed.remove(product_id)

    viewed.insert(0, product_id)
    session["recently_viewed"] = viewed[:4]
    session.modified = True


def add_products():
    if Product.query.first():
        return

    products = [
        Product(
            name="Cold Pressed Groundnut Oil",
            price=220,
            old_price=299,
            discount_pct=26,
            image="oil1.jpg",
            category="Oils",
            stock=50
        ),
        Product(
            name="Organic Seeds Pack",
            price=150,
            old_price=199,
            discount_pct=24,
            image="seeds.jpg",
            category="Seeds",
            stock=100
        ),
        Product(
            name="Traditional Mango Pickle",
            price=180,
            old_price=249,
            discount_pct=27,
            image="pickle.jpg",
            category="Pickles",
            stock=30
        ),
    ]

    db.session.add_all(products)
    db.session.commit()

def add_reviews():
    if Review.query.first():
        return

    reviews = [
        Review(product_id=1, user_name="Aarti D.", rating=5, comment="Excellent quality!"),
        Review(product_id=1, user_name="Anil K.", rating=4, comment="Very good oil."),
        Review(product_id=2, user_name="Priya N.", rating=5, comment="Fresh and organic."),
    ]

    db.session.add_all(reviews)
    db.session.commit()

def send_admin_email(subject, body):
    sender_email = "youremail@gmail.com"
    sender_password = "your_app_password"
    admin_email = "youremail@gmail.com"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = admin_email

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
    except:
        pass

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    add_products()
    add_reviews()

    reviews = Review.query.all()
    mid = len(reviews) // 2
    reviews_row1 = reviews[:mid]
    reviews_row2 = reviews[mid:]

    heroes = Hero.query.all()
    hero = heroes[0] if heroes else None

    videos = Video.query.all()

    products = Product.query.all()

    return render_template(
        "home.html",
        products=products,
        best_products=products,        # temporary safe fallback
        featured_products=products,    # temporary safe fallback
        recently_viewed=Product.query.filter(
            Product.id.in_(session.get("recently_viewed", []))
        ).all(),
        reviews_row1=reviews_row1,
        reviews_row2=reviews_row2,
        hero=hero,
        videos=videos
    )


@app.route("/products")
def products_page():
    category = request.args.get("category")

    # Add price range filters
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)

    query = Product.query

    if category:
        query = query.filter_by(category=category)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)


    products = query.all()
    categories = Category.query.all()

    return render_template(
        "products.html",
        products=products,
        categories=categories
    )


@app.route("/cart-count")
def cart_count():
    cart = session.get("cart", {})
    count = sum(cart.values())
    return {"count": count}

@app.route("/add-review/<int:product_id>", methods=["POST"])
def add_review(product_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    if not user:
        return redirect(url_for("login"))

    rating = int(request.form["rating"])
    comment = request.form["comment"]

    product = db.session.get(Product, product_id)

    # check if user purchased this product
    purchased = OrderItem.query.filter_by(
        product_name=product.name
    ).first()

    review = Review(
        product_id=product_id,
        user_name=user.name,
        rating=rating,
        comment=comment,
        approved=False,
        verified=bool(purchased)
    )

    db.session.add(review)
    db.session.commit()

    return redirect(url_for("product_detail", product_id=product_id))


# ---------------- PRODUCT DETAIL ----------------

@app.route("/product/<int:product_id>")
def product_detail(product_id):

    product = Product.query.get_or_404(product_id)
    add_recently_viewed(product.id)

    sort = request.args.get("sort")

    query = Review.query.filter_by(product_id=product.id, approved=True)

    if sort == "high":
        query = query.order_by(Review.rating.desc())
    elif sort == "low":
        query = query.order_by(Review.rating.asc())
    else:
        query = query.order_by(Review.id.desc())  # latest

    reviews = query.all()


    review_count = len(reviews)

    # Average rating
    if review_count > 0:
        avg_rating = round(sum(r.rating for r in reviews) / review_count, 1)
    else:
        avg_rating = 0

    # Rating counts (1–5 stars)
    rating_counts = {i: 0 for i in range(1, 6)}

    for r in reviews:
        if r.rating in rating_counts:
            rating_counts[r.rating] += 1

    return render_template(
        "product_detail.html",
        product=product,
        variants=product.variants,
        reviews=reviews,
        avg_rating=avg_rating,
        review_count=review_count,
        rating_counts=rating_counts
    )

# ---------------- CART ----------------

@app.route("/add-to-cart/<int:variant_id>")
def add_to_cart(variant_id):
    variant = ProductVariant.query.get(variant_id)

    if not variant or variant.stock <= 0:
        return jsonify({"status": "out_of_stock"})

    cart = session.get("cart", {})

    key = f"v{variant_id}"
    cart[key] = cart.get(key, 0) + 1

    session["cart"] = cart

    count = sum(cart.values())

    return jsonify({
        "status": "ok",
        "count": count
    })

@app.route("/remove-from-cart/<int:variant_id>")
def remove_from_cart(variant_id):
    cart = session.get("cart", {})

    key = f"v{variant_id}"
    cart.pop(key, None)

    session["cart"] = cart
    session.modified = True

    return redirect(url_for("cart_page"))


@app.route("/cart")
def cart_page():
    cart = session.get("cart", {})
    cart_items = []
    total = 0

    for variant_key, qty in cart.items():
        variant_id = int(variant_key.replace("v", ""))
        variant = db.session.get(ProductVariant, variant_id)

        if not variant:
            continue

        product = variant.product

        subtotal = variant.price * qty
        total += subtotal

        cart_items.append({
            "product": product,
            "variant": variant,
            "quantity": qty,
            "subtotal": subtotal
        })

    return render_template("cart.html",
                           cart_items=cart_items,
                           total=total)


@app.route("/clear-cart")
def clear_cart():
    session.pop("cart", None)
    return redirect(url_for("cart_page"))         # ← also updated here


# ---------------- CHECKOUT FROM CART ----------------

@app.route("/checkout-cart")
def checkout_cart():
    cart = session.get("cart", {})
    items = []
    total = 0

    for variant_key, qty in cart.items():
        variant_id = int(variant_key.replace("v", ""))
        variant = db.session.get(ProductVariant, variant_id)

        if not variant:
            continue

        product = variant.product

        subtotal = variant.price * qty
        total += subtotal

        items.append({
            "product": product,
            "variant": variant,
            "quantity": qty,
            "subtotal": subtotal
        })

    return render_template("checkout_cart.html",
                           items=items,
                           total=total)

@app.route("/confirm-cart-order", methods=["POST"])
def confirm_cart_order():
    cart = session.get("cart", {})
    checkout_data = session.get("checkout_data")

    if not cart or not checkout_data:
        return redirect(url_for("products_page"))

    total = 0

    order = Order(
        date=datetime.now().strftime("%d-%m-%Y %H:%M"),
        total_price=0,
        payment_method="COD",
        customer_name=checkout_data["name"],
        customer_phone=checkout_data["phone"],
        customer_address=checkout_data["address"],
        status="Pending"
    )
    db.session.add(order)

    for variant_key, qty in cart.items():
        variant_id = int(variant_key.replace("v", ""))
        variant = db.session.get(ProductVariant, variant_id)

        if not variant:
            continue

        # STOCK CHECK
        if variant.stock < qty:
            return "Not enough stock for " + variant.product.name

        # Deduct stock
        variant.stock -= qty

        product = variant.product
        subtotal = variant.price * qty
        total += subtotal

        order_item = OrderItem(
            order_id=order.id,
            product_name=product.name,
            price=variant.price,
            quantity=qty
        )
        db.session.add(order_item)

    order.total_price = total
    db.session.commit()

    session["cart"] = {}

    return redirect(url_for("order_success"))

# ---------------- BUY NOW ----------------

@app.route("/buy-now/<int:variant_id>")
def buy_now(variant_id):
    variant = db.session.get(ProductVariant, variant_id)

    if not variant or variant.stock <= 0:
        return redirect(url_for("products_page"))

    # create temporary cart with only this item
    session["cart"] = {f"v{variant_id}": 1}

    return redirect(url_for("checkout_cart"))

# ---------------- PAYMENT PAGE ----------------

@app.route("/payment/<int:id>", methods=["POST"])
def payment_page(id):

    product = db.session.get(Product, id)

    if not product:
        return redirect(url_for("products_page"))

    # store checkout details in session
    session["checkout_data"] = {
        "name": request.form["name"],
        "phone": request.form["phone"],
        "address": request.form["address"]
    }

    return render_template("payment.html", product=product)

@app.route("/payment-cart", methods=["POST"])
def payment_cart():
    cart = session.get("cart", {})

    if not cart:
        return redirect(url_for("products_page"))

    # save checkout data
    session["checkout_data"] = {
        "name": request.form["name"],
        "phone": request.form["phone"],
        "address": request.form["address"]
    }

    cart_items = []
    total = 0

    for variant_key, qty in cart.items():

        variant_id = int(variant_key.replace("v", ""))
        variant = db.session.get(ProductVariant, variant_id)

        if not variant:
            continue

        product = variant.product
        subtotal = variant.price * qty
        total += subtotal

        cart_items.append({
            "product": product,
            "variant": variant,
            "quantity": qty,
            "subtotal": subtotal
        })

    return render_template(
        "payment_cart.html",
        cart_items=cart_items,
        total=total,
        old_price=total,
        discount=0
    )

@app.route("/confirm-order/<int:id>", methods=["POST"])
def confirm_order(id):

    product = db.session.get(Product, id)

    product.stock = max(product.stock - 1, 0)


    if not product:
        return redirect(url_for("products_page"))

    checkout_data = session.get("checkout_data", {})

    name = checkout_data.get("name")
    phone = checkout_data.get("phone")
    address = checkout_data.get("address")

    payment = request.form["payment"]

    # If UPI selected, go to UPI payment screen
    if payment == "UPI":
        session["product_id"] = id
        session["payment_method"] = payment
        return redirect(url_for("upi_payment"))

    order = Order(
        date=datetime.now().strftime("%d-%m-%Y %H:%M"),
        total_price=product.price,
        payment_method=payment,
        customer_name=name,
        customer_phone=phone,
        customer_address=address,
        status="Pending"
    )

    db.session.add(order)
    db.session.commit()

    item = OrderItem(
        order_id=order.id,
        product_name=product.name,
        price=product.price,
        quantity=1
    )

    db.session.add(item)
    db.session.commit()

    return redirect(url_for("order_success"))

# ---------------- UPI PAYMENT ----------------

@app.route("/upi-payment")
def upi_payment():

    product_id = session.get("product_id")
    product = db.session.get(Product, product_id)

    if not product:
        return redirect(url_for("products_page"))

    return render_template("upi_payment.html", product=product)

@app.route("/confirm-upi-payment")
def confirm_upi_payment():

    product_id = session.get("product_id")
    payment = session.get("payment_method", "UPI")

    product = db.session.get(Product, product_id)

    if not product:
        return redirect(url_for("products_page"))

    order = Order(
        date=datetime.now().strftime("%d-%m-%Y %H:%M"),
        total_price=product.price,
        payment_method=payment
    )

    db.session.add(order)
    db.session.commit()

    item = OrderItem(
        order_id=order.id,
        product_name=product.name,
        price=product.price,
        quantity=1
    )

    db.session.add(item)
    db.session.commit()

    return redirect(url_for("order_success"))


# ---------------- ORDERS ----------------

@app.route("/orders")
def orders():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_orders = Order.query.order_by(Order.id.desc()).all()
    return render_template("orders.html", orders=user_orders)



# ---------------- ORDER SUCCESS ----------------

@app.route("/order-success")
def order_success():
    return render_template("order_success.html")

# ---------------- CONTACT ----------------
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        content = request.form["message"]

        msg = Message(
            name=name,
            email=email,
            content=content,
            date=datetime.now().strftime("%d-%m-%Y %H:%M")
        )

        db.session.add(msg)
        db.session.commit()

        # Send email notification
        send_admin_email(
            "New Customer Message",
            f"Name: {name}\nEmail: {email}\nMessage:\n{content}"
        )

        return render_template("contact.html", success=True)

    return render_template("contact.html")

@app.route("/track-order", methods=["GET", "POST"])
def track_order():
    order = None
    error = None

    if request.method == "POST":
        raw_id = request.form.get("order_id", "").strip()

        # extract only numbers
        order_id = "".join(filter(str.isdigit, raw_id))

        if order_id:
            order = Order.query.get(int(order_id))

        if not order:
            error = "Order not found"

    return render_template("track_order.html", order=order, error=error)



# ---------------- LOGIN ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            return redirect(url_for('home'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if password != confirm:
            return render_template('register.html', error="Passwords don't match")

        if User.query.filter_by(email=email).first():
            return render_template('register.html', error="Email already registered")

        hashed = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    return redirect("/")

from flask import flash

@app.route("/account", methods=["GET", "POST"])
def account():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user = db.session.get(User, user_id)

    if request.method == "POST":
        user.name = request.form["name"]
        user.email = request.form["email"]
        user.phone = request.form["phone"]
        user.address = request.form["address"]

        db.session.commit()

        session["user_name"] = user.name
        flash("Details updated successfully", "success")

        return redirect(url_for("account"))

    return render_template("account.html", user=user)

# ---------------- ADMIN PAGE ----------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    total_users = User.query.count()
    total_orders = Order.query.count()
    total_products = Product.query.count()

    total_revenue = db.session.query(
        db.func.sum(Order.total_price)
    ).scalar() or 0

    # Last 7 days revenue and orders
    from collections import defaultdict
    revenue_data = defaultdict(int)
    order_data = defaultdict(int)

    orders = Order.query.all()

    for order in orders:
        date = order.date.split(" ")[0]
        revenue_data[date] += order.total_price
        order_data[date] += 1

    labels = list(revenue_data.keys())[-7:]
    revenues = [revenue_data[d] for d in labels]
    order_counts = [order_data[d] for d in labels]

    # Recent orders
    recent_orders = Order.query.order_by(Order.id.desc()).limit(5).all()

    # Order status breakdown
    status_counts = {
        "Pending": Order.query.filter_by(status="Pending").count(),
        "Shipped": Order.query.filter_by(status="Shipped").count(),
        "Delivered": Order.query.filter_by(status="Delivered").count(),
    }

    from sqlalchemy import func

    # Top selling products
    top_products = (
        db.session.query(
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label("total_sold")
        )
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )

    # Low stock products
    low_stock = Product.query.filter(Product.stock < 10).all()


    return render_template(
    "admin/dashboard.html",
    total_users=total_users,
    total_orders=total_orders,
    total_products=total_products,
    total_revenue=total_revenue,
    chart_labels=labels,
    revenue_values=revenues,
    order_values=order_counts,
    recent_orders=recent_orders,
    status_counts=status_counts,
    top_products=top_products,
    low_stock=low_stock
)

@app.route("/admin/export-orders")
def export_orders():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    import csv
    from io import StringIO
    from flask import Response

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Order ID", "Customer", "Phone", "Total", "Status", "Date"])

    orders = Order.query.all()
    for o in orders:
        writer.writerow([
            o.id,
            o.customer_name,
            o.customer_phone,
            o.total_price,
            o.status,
            o.date
        ])

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=orders.csv"}
    )



# ---------------- ADMIN PRODUCTS ----------------

@app.route("/admin/products")
def admin_products():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    products = Product.query.all()

    # get unique categories from existing products
    categories = db.session.query(Product.category).distinct().all()
    categories = [{"name": c[0]} for c in categories if c[0]]

    # fallback categories if database empty
    if not categories:
        categories = [
            {"name": "Oils"},
            {"name": "Seeds"},
            {"name": "Pickles"}
        ]

    return render_template(
        "admin/products.html",
        products=products,
        categories=categories
    )

@app.route("/admin/products/add", methods=["POST"])
def admin_add_product():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    name = request.form["name"]
    category = request.form["category"]

    image_file = request.files["image"]
    filename = ""
    if image_file:
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image_file.save(image_path)

    # create product
    product = Product(
        name=name,
        price=0,  # base price not used when variants exist
        image=filename,
        category=category,
        stock=0
    )
    db.session.add(product)
    db.session.commit()

    # create variants
    quantities = request.form.getlist("quantity")
    prices = request.form.getlist("variant_price")
    stocks = request.form.getlist("variant_stock")

    for q, p, s in zip(quantities, prices, stocks):
        if q and p and s:
            variant = ProductVariant(
                product_id=product.id,
                quantity=q,
                price=float(p),
                stock=int(s)
            )
            db.session.add(variant)

    db.session.commit()

    return redirect(url_for("admin_products"))

@app.route("/admin/products/delete/<int:id>")
def admin_delete_product(id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()

    return redirect(url_for("admin_products"))

@app.route("/admin/products/edit/<int:id>", methods=["GET", "POST"])
def admin_edit_product(id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    product = Product.query.get_or_404(id)

    if request.method == "POST":
        # Update basic product info
        product.name = request.form.get("name")
        product.category = request.form.get("category")
        product.description = request.form.get("description")

        # Optional: fallback price if no variants
        if request.form.get("price"):
            product.price = float(request.form.get("price"))

        # ===== VARIANT UPDATE =====
        quantities = request.form.getlist("variant_quantity[]")
        prices = request.form.getlist("variant_price[]")
        stocks = request.form.getlist("variant_stock[]")

        # Delete old variants
        ProductVariant.query.filter_by(product_id=product.id).delete()

        # Add new variants
        for i in range(len(quantities)):
            q = quantities[i].strip()
            p = prices[i].strip()
            s = stocks[i].strip()

            if q and p:
                variant = ProductVariant(
                    product_id=product.id,
                    quantity=q,
                    price=float(p),
                    stock=int(s) if s else 0
                )
                db.session.add(variant)

        db.session.commit()
        return redirect(url_for("admin_products"))

    return render_template("admin/edit_product.html", product=product)


@app.route("/admin/products/update/<int:id>", methods=["POST"])
def admin_update_product(id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    product = db.session.get(Product, id)

    # Basic fields
    product.name = request.form["name"]
    product.price = float(request.form["price"])
    product.category = request.form["category"]

    # Checkbox handling
    product.is_best = "is_best" in request.form
    product.is_featured = "is_featured" in request.form

    # Safe image handling
    image_file = request.files.get("image")

    if image_file and image_file.filename:
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image_file.save(image_path)
        product.image = filename

    db.session.commit()

    return redirect(url_for("admin_products"))


@app.route("/admin/orders")
def admin_orders():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    orders = Order.query.order_by(Order.id.desc()).all()
    return render_template("admin/orders.html", orders=orders)

@app.route("/admin/orders/update-status/<int:id>")
def update_order_status(id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    order = Order.query.get_or_404(id)

    if order.status == "Pending":
        order.status = "Shipped"
    elif order.status == "Shipped":
        order.status = "Delivered"

    db.session.commit()
    return redirect("/admin/orders")

@app.route("/admin/customers")
def admin_customers():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    users = User.query.order_by(User.id.desc()).all()
    return render_template("admin/customers.html", users=users)

@app.route("/admin/payments")
def admin_payments():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    orders = Order.query.order_by(Order.id.desc()).all()
    return render_template("admin/payments.html", orders=orders)

@app.route("/admin/categories")
def admin_categories():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    categories = Category.query.all()
    return render_template("admin/categories.html", categories=categories)

@app.route("/admin/categories/add", methods=["POST"])
def add_category():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    name = request.form["name"]

    new_cat = Category(name=name)

    db.session.add(new_cat)
    db.session.commit()

    return redirect("/admin/categories")

@app.route("/admin/categories/delete/<int:id>")
def delete_category(id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    cat = Category.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()

    return redirect("/admin/categories")

@app.route("/admin/coupons")
def admin_coupons():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    coupons = Coupon.query.all()
    return render_template("admin/coupons.html", coupons=coupons)

@app.route("/admin/coupons/add", methods=["POST"])
def add_coupon():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")
    code = request.form["code"]
    discount = request.form["discount"]

    new_coupon = Coupon(code=code, discount=discount)
    db.session.add(new_coupon)
    db.session.commit()

    return redirect("/admin/coupons")

@app.route("/admin/coupons/delete/<int:id>")
def delete_coupon(id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    coupon = Coupon.query.get_or_404(id)
    db.session.delete(coupon)
    db.session.commit()

    return redirect("/admin/coupons")

@app.route("/admin/hero", methods=["GET", "POST"])
def admin_hero():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")


    if request.method == "POST":
        title = request.form["title"]
        subtitle = request.form["subtitle"]

        image_file = request.files["image"]

        filename = ""
        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(image_path)

        hero = Hero(title=title, subtitle=subtitle, image=filename)
        db.session.add(hero)
        db.session.commit()

    hero = Hero.query.first()
    return render_template("admin/hero.html", hero=hero)


@app.route("/admin/hero/add", methods=["POST"])
def add_hero():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    title = request.form["title"]
    subtitle = request.form["subtitle"]

    image_file = request.files["image"]

    filename = ""
    if image_file and image_file.filename != "":
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image_file.save(image_path)

    hero = Hero(title=title, subtitle=subtitle, image=filename)
    db.session.add(hero)
    db.session.commit()

    return redirect("/admin/hero")

@app.route("/admin/hero/delete/<int:id>")
def delete_hero(id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    hero = Hero.query.get_or_404(id)
    db.session.delete(hero)
    db.session.commit()

    return redirect("/admin/hero")

@app.route("/admin/messages")
def admin_messages():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    messages = Message.query.order_by(Message.id.desc()).all()
    return render_template("admin/messages.html", messages=messages)

@app.route("/admin/messages/delete/<int:id>")
def delete_message(id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    msg = Message.query.get_or_404(id)
    db.session.delete(msg)
    db.session.commit()

    return redirect("/admin/messages")

@app.route("/admin/videos")
def admin_videos():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    videos = Video.query.all()
    variants = ProductVariant.query.all()

    return render_template(
        "admin/videos.html",
        videos=videos,
        variants=variants
    )

@app.route("/admin/videos/add", methods=["POST"])
def add_video():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    title = request.form["title"]
    url = request.form["url"]

    video = Video(title=title, url=url)
    db.session.add(video)
    db.session.commit()

    return redirect("/admin/videos")

@app.route("/admin/videos/delete/<int:id>")
def delete_video(id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    video = Video.query.get_or_404(id)
    db.session.delete(video)
    db.session.commit()

    return redirect("/admin/videos")

@app.route("/admin/settings")
def admin_settings():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    settings = Setting.query.first()
    return render_template("admin/settings.html", settings=settings)

@app.route("/admin/settings/update", methods=["POST"])
def update_settings():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    settings = Setting.query.first()

    if not settings:
        settings = Setting()
        db.session.add(settings)

    settings.store_name = request.form["store_name"]
    settings.email = request.form["email"]
    settings.phone = request.form["phone"]
    settings.address = request.form["address"]

    db.session.commit()

    return redirect("/admin/settings")

@app.route("/admin/reviews/delete/<int:id>")
def delete_review(id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    review = Review.query.get_or_404(id)
    db.session.delete(review)
    db.session.commit()

    return redirect("/admin/reviews")

@app.route("/admin/reviews")
def admin_reviews():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    reviews = Review.query.order_by(Review.id.desc()).all()
    return render_template("admin/reviews.html", reviews=reviews)


@app.route("/admin/reviews/approve/<int:id>")
def approve_review(id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    review = Review.query.get_or_404(id)
    review.approved = True
    db.session.commit()

    return redirect(url_for("admin_reviews"))


# ---------------- ADMIN LOGIN ----------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password, password):
            session["admin_logged_in"] = True
            session["admin_id"] = admin.id
            return redirect(url_for("admin_dashboard"))
        else:
            return render_template("admin/login.html", error="Invalid credentials")

    # This ensures GET always returns the login page
    return render_template("admin/login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)



