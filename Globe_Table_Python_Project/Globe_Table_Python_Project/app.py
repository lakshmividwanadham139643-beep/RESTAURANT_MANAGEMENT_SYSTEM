from __future__ import annotations
import csv, io, os, sqlite3
from datetime import datetime, date
from functools import wraps
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response, abort

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "globe_table.db"
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("GLOBE_TABLE_SECRET", "change-this-secret-before-deployment")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

MENU = [
("Gongura chicken",320,"Mains",0,"🍗","Andhra"),("Guntur chilli prawns",420,"Starters",0,"🦐","Andhra"),
("Chilli chicken 65",260,"Starters",0,"🌶️","Andhra"),("Pappu and avakaya meal",200,"Mains",1,"🍲","Andhra"),
("Pootharekulu",120,"Sweets",1,"🍬","Andhra"),("Hyderabadi dum biryani",360,"Rice",0,"🍛","Hyderabadi"),
("Mutton haleem",300,"Mains",0,"🥣","Hyderabadi"),("Double ka meetha",150,"Sweets",1,"🍮","Hyderabadi"),
("Paneer tikka",280,"Starters",1,"🧀","North Indian"),("Butter chicken",340,"Mains",0,"🍗","North Indian"),
("Dal makhani",240,"Mains",1,"🍲","North Indian"),("Garlic naan",60,"Mains",1,"🫓","North Indian"),
("Veg pulao",220,"Rice",1,"🍚","North Indian"),("Gulab jamun",110,"Sweets",1,"🍩","North Indian"),
("Mango lassi",110,"Drinks",1,"🥭","North Indian"),("Ghee podi dosa",140,"Mains",1,"🥞","South Indian"),
("Idli sambar",110,"Mains",1,"🍘","South Indian"),("Kerala fish curry",380,"Mains",0,"🐟","South Indian"),
("Filter coffee",70,"Drinks",1,"☕","South Indian"),("Buttermilk",60,"Drinks",1,"🥛","South Indian"),
("Veg Manchurian",220,"Starters",1,"🥡","Chinese"),("Chicken dim sum",260,"Starters",0,"🥟","Chinese"),
("Hakka noodles",240,"Mains",1,"🍜","Chinese"),("Kung pao chicken",320,"Mains",0,"🥡","Chinese"),
("Egg fried rice",200,"Rice",0,"🍳","Chinese"),("Bruschetta",200,"Starters",1,"🍞","Italian"),
("Margherita pizza",380,"Mains",1,"🍕","Italian"),("Spaghetti bolognese",380,"Mains",0,"🍝","Italian"),
("Penne alfredo",340,"Mains",1,"🍝","Italian"),("Tiramisu",240,"Sweets",1,"🍰","Italian"),
("Cappuccino",130,"Drinks",1,"☕","Italian"),("Veg tacos",240,"Starters",1,"🌮","Mexican"),
("Nachos with guacamole",220,"Starters",1,"🥑","Mexican"),("Chicken burrito",320,"Mains",0,"🌯","Mexican"),
("Churros with chocolate",160,"Sweets",1,"🥨","Mexican"),("Tom yum soup",280,"Starters",0,"🍲","Thai"),
("Pad Thai",340,"Mains",0,"🍜","Thai"),("Thai green curry",360,"Mains",1,"🍛","Thai"),
("Mango sticky rice",200,"Sweets",1,"🥭","Thai"),("Veg sushi roll",320,"Starters",1,"🍣","Japanese"),
("Salmon nigiri",520,"Starters",0,"🍣","Japanese"),("Chicken ramen",400,"Mains",0,"🍜","Japanese"),
("Matcha ice cream",180,"Sweets",1,"🍵","Japanese"),("Korean fried chicken",380,"Starters",0,"🍗","Korean"),
("Tteokbokki",260,"Starters",1,"🌶️","Korean"),("Bibimbap",360,"Rice",0,"🍚","Korean"),
("Kimchi fried rice",300,"Rice",0,"🍚","Korean"),("Hummus with pita",200,"Starters",1,"🫓","Middle Eastern"),
("Falafel wrap",220,"Mains",1,"🧆","Middle Eastern"),("Chicken shawarma",260,"Mains",0,"🥙","Middle Eastern"),
("Baklava",180,"Sweets",1,"🍯","Middle Eastern"),("Adana kebab",420,"Mains",0,"🍢","Turkish"),
("Turkish coffee",120,"Drinks",1,"☕","Turkish"),("Turkish delight",150,"Sweets",1,"🍬","Turkish"),
("Greek salad",240,"Starters",1,"🥗","Greek"),("Chicken souvlaki",340,"Mains",0,"🍢","Greek"),
("Moussaka",380,"Mains",0,"🍆","Greek"),("French onion soup",260,"Starters",1,"🧅","French"),
("Ratatouille",300,"Mains",1,"🍆","French"),("Crème brûlée",260,"Sweets",1,"🍮","French"),
("Butter croissant",120,"Sweets",1,"🥐","French"),("Paella",480,"Rice",0,"🥘","Spanish"),
("Patatas bravas",200,"Starters",1,"🥔","Spanish"),("Cheeseburger",320,"Mains",0,"🍔","American"),
("Buffalo wings",340,"Starters",0,"🍗","American"),("Mac and cheese",260,"Mains",1,"🧀","American"),
("French fries",120,"Starters",1,"🍟","American"),("Chocolate brownie",180,"Sweets",1,"🍫","American"),
("Fish and chips",400,"Mains",0,"🐟","British"),("Sticky toffee pudding",240,"Sweets",1,"🍮","British"),
("Bratwurst with sauerkraut",380,"Mains",0,"🌭","German"),("Apple strudel",220,"Sweets",1,"🍎","German"),
("Borscht",240,"Starters",1,"🥣","Russian"),("Beef stroganoff",420,"Mains",0,"🥩","Russian"),
("Pho",340,"Mains",0,"🍜","Vietnamese"),("Fresh spring rolls",220,"Starters",1,"🌯","Vietnamese"),
("Nasi goreng",300,"Rice",0,"🍛","Indonesian"),("Chicken satay",280,"Starters",0,"🍢","Indonesian"),
("Doro wat with injera",400,"Mains",0,"🍲","Ethiopian"),("Chicken tagine",420,"Mains",0,"🍲","Moroccan"),
("Vegetable couscous",260,"Mains",1,"🥘","Moroccan"),("Feijoada",420,"Mains",0,"🥘","Brazilian"),
("Pão de queijo",160,"Starters",1,"🧀","Brazilian"),("Jerk chicken",380,"Mains",0,"🍗","Caribbean"),
("Virgin mojito",150,"Drinks",1,"🍹","Caribbean")
]

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'customer', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS menu(id INTEGER PRIMARY KEY, name TEXT NOT NULL, price INTEGER NOT NULL CHECK(price>0), category TEXT NOT NULL, vegetarian INTEGER NOT NULL, emoji TEXT NOT NULL, cuisine TEXT NOT NULL, available INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id), customer_name TEXT NOT NULL, phone TEXT NOT NULL, email TEXT NOT NULL, delivery_address TEXT NOT NULL, billing_name TEXT NOT NULL, billing_address TEXT NOT NULL, gstin TEXT, payment_method TEXT NOT NULL, spice TEXT, instructions TEXT, subtotal INTEGER NOT NULL, gst INTEGER NOT NULL, discount INTEGER NOT NULL, total INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'Received', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE, menu_id INTEGER, item_name TEXT NOT NULL, price INTEGER NOT NULL, quantity INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS reservations(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users(id), name TEXT NOT NULL, phone TEXT NOT NULL, booking_date TEXT NOT NULL, booking_time TEXT NOT NULL, guests INTEGER NOT NULL, code TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS parties(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users(id), name TEXT NOT NULL, phone TEXT NOT NULL, event TEXT NOT NULL, event_date TEXT NOT NULL, guests INTEGER NOT NULL, package TEXT NOT NULL, estimate INTEGER NOT NULL, created_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
        """)
        if c.execute("SELECT COUNT(*) FROM menu").fetchone()[0] == 0:
            c.executemany("INSERT INTO menu(name,price,category,vegetarian,emoji,cuisine) VALUES(?,?,?,?,?,?)", MENU)
        if not c.execute("SELECT id FROM users WHERE email='admin@globetable.local'").fetchone():
            c.execute("INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)",
                      ("Globe Table Admin","admin@globetable.local",generate_password_hash("Admin@123"),"admin",datetime.now().isoformat(timespec="seconds")))

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please login to continue.", "error")
            return redirect(url_for("index"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please login to continue.", "error")
            return redirect(url_for("index"))
        if session.get("role") != "admin":
            abort(403)
        return fn(*args, **kwargs)
    return wrapper

@app.context_processor
def inject_globals():
    return {"current_user": session.get("user_name"), "current_role": session.get("role")}

@app.get("/")
def index():
    with db() as c:
        items = c.execute("SELECT * FROM menu WHERE available=1 ORDER BY cuisine,name").fetchall()
    cuisines = sorted({x["cuisine"] for x in items})
    return render_template("index.html", menu=items, cuisines=cuisines)

@app.post("/register")
def register():
    name=request.form.get("name","").strip()
    email=request.form.get("email","").strip().lower()
    password=request.form.get("password","")
    if not name or "@" not in email or len(password)<6:
        flash("Enter a name, valid email and password with at least 6 characters.", "error")
        return redirect(url_for("index"))
    try:
        with db() as c:
            c.execute("INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)",
                      (name,email,generate_password_hash(password),"customer",datetime.now().isoformat(timespec="seconds")))
        flash("Account created. You can now login.", "success")
    except sqlite3.IntegrityError:
        flash("That email is already registered. Please login.", "error")
    return redirect(url_for("index"))

@app.post("/login")
def login():
    email=request.form.get("email","").strip().lower()
    password=request.form.get("password","")
    with db() as c:
        user=c.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
    if not user or not check_password_hash(user["password_hash"],password):
        flash("Invalid email or password.", "error")
        return redirect(url_for("index"))
    session.clear()
    session.update(user_id=user["id"],user_name=user["name"],user_email=user["email"],role=user["role"])
    flash(f"Welcome, {user['name']}!", "success")
    return redirect(url_for("index"))

@app.post("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "success")
    return redirect(url_for("index"))

@app.post("/api/order")
@login_required
def create_order():
    data=request.get_json(silent=True) or {}
    required=["name","phone","email","address","billing_name","billing_address","payment","items"]
    if any(not data.get(k) for k in required) or not isinstance(data.get("items"),list) or not data["items"]:
        return jsonify(error="Please complete all required customer, billing and cart details."),400
    if not data["phone"].isdigit() or len(data["phone"])!=10:
        return jsonify(error="Enter a valid 10-digit phone number."),400
    subtotal=0; clean=[]
    with db() as c:
        for entry in data["items"]:
            try: item_id=int(entry["id"]); qty=int(entry["qty"])
            except (KeyError,TypeError,ValueError): return jsonify(error="Invalid cart item."),400
            if qty<1 or qty>50: return jsonify(error="Quantity must be between 1 and 50."),400
            item=c.execute("SELECT * FROM menu WHERE id=? AND available=1",(item_id,)).fetchone()
            if not item: return jsonify(error="A selected dish is unavailable. Refresh the menu."),400
            subtotal += item["price"]*qty
            clean.append((item,qty))
        discount=round(subtotal*.10) if data.get("coupon","").upper()=="GLOBE10" else 0
        gst=round(subtotal*.05)
        total=subtotal+gst-discount
        cur=c.execute("""INSERT INTO orders(user_id,customer_name,phone,email,delivery_address,billing_name,billing_address,gstin,payment_method,spice,instructions,subtotal,gst,discount,total,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (session["user_id"],data["name"].strip(),data["phone"],data["email"].strip(),data["address"].strip(),data["billing_name"].strip(),data["billing_address"].strip(),data.get("gstin",""),data["payment"],data.get("spice","Medium"),data.get("instructions",""),subtotal,gst,discount,total,"Received",datetime.now().isoformat(timespec="seconds")))
        order_id=cur.lastrowid
        c.executemany("INSERT INTO order_items(order_id,menu_id,item_name,price,quantity) VALUES(?,?,?,?,?)",
                      [(order_id,item["id"],item["name"],item["price"],qty) for item,qty in clean])
    return jsonify(ok=True,order_id=order_id,receipt=f"GT-{order_id}",subtotal=subtotal,gst=gst,discount=discount,total=total),201

@app.get("/api/orders/<int:order_id>")
@login_required
def order_details(order_id):
    with db() as c:
        order=c.execute("SELECT * FROM orders WHERE id=? AND user_id=?",(order_id,session["user_id"])).fetchone()
        if not order: abort(404)
        items=c.execute("SELECT item_name,price,quantity FROM order_items WHERE order_id=?",(order_id,)).fetchall()
    return jsonify(order=dict(order),items=[dict(x) for x in items])

@app.get("/my-orders")
@login_required
def my_orders():
    with db() as c:
        orders=c.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC",(session["user_id"],)).fetchall()
    return render_template("orders.html",orders=orders)

@app.post("/reserve")
@login_required
def reserve():
    name=request.form.get("name","").strip(); phone=request.form.get("phone","").strip()
    day=request.form.get("date",""); time=request.form.get("time",""); guests=int(request.form.get("guests",2))
    if not name or not phone.isdigit() or len(phone)!=10 or not day or day<date.today().isoformat() or guests not in (1,2,3,4,5,6,7,8):
        flash("Check your reservation details. Use a future date and a valid phone number.", "error")
    else:
        import secrets
        code="GT"+secrets.token_hex(2).upper()
        with db() as c:
            c.execute("INSERT INTO reservations(user_id,name,phone,booking_date,booking_time,guests,code,created_at) VALUES(?,?,?,?,?,?,?,?)",
                      (session["user_id"],name,phone,day,time,guests,code,datetime.now().isoformat(timespec="seconds")))
        flash(f"Reservation confirmed. Reference: {code}", "success")
    return redirect(url_for("index")+"#reserve")

@app.post("/party")
@login_required
def party():
    name=request.form.get("name","").strip(); phone=request.form.get("phone","").strip()
    event=request.form.get("event","Birthday"); day=request.form.get("date","")
    try: guests=int(request.form.get("guests","20")); package=request.form.get("package","599")
    except ValueError: guests=0; package="599"
    rates={"599":599,"899":899,"1299":1299}
    if not name or not phone.isdigit() or len(phone)!=10 or guests<10 or guests>80 or package not in rates or not day or day<date.today().isoformat():
        flash("Please check party details (10–80 guests and a future date).","error")
    else:
        estimate=round(guests*rates[package]*1.05)
        with db() as c:
            c.execute("INSERT INTO parties(user_id,name,phone,event,event_date,guests,package,estimate,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                      (session["user_id"],name,phone,event,day,guests,package,estimate,datetime.now().isoformat(timespec="seconds")))
        flash(f"Party enquiry saved. Estimated amount including 5% GST: ₹{estimate:,}.","success")
    return redirect(url_for("index")+"#party")

@app.get("/admin")
@login_required
@admin_required
def admin():
    with db() as c:
        orders=c.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
        reservations=c.execute("SELECT * FROM reservations ORDER BY id DESC").fetchall()
        parties=c.execute("SELECT * FROM parties ORDER BY id DESC").fetchall()
        items=c.execute("SELECT * FROM menu ORDER BY id").fetchall()
        customers=c.execute("SELECT id,name,email,created_at FROM users WHERE role='customer' ORDER BY id DESC").fetchall()
        stats={"orders":c.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
               "sales":c.execute("SELECT COALESCE(SUM(total),0) FROM orders").fetchone()[0],
               "customers":len(customers),"reservations":len(reservations)}
    return render_template("admin.html",orders=orders,reservations=reservations,parties=parties,items=items,customers=customers,stats=stats)

@app.post("/admin/menu/add")
@login_required
@admin_required
def add_menu():
    name=request.form.get("name","").strip()
    try: price=int(request.form.get("price","0"))
    except ValueError: price=0
    if not name or price<1:
        flash("Dish name and a positive price are required.","error")
    else:
        with db() as c:
            c.execute("INSERT INTO menu(name,price,category,vegetarian,emoji,cuisine) VALUES(?,?,?,?,?,?)",
                      (name,price,request.form.get("category","Mains"),1 if request.form.get("vegetarian") else 0,"🍽️",request.form.get("cuisine","Chef Special")))
        flash("Dish added.","success")
    return redirect(url_for("admin"))

@app.post("/admin/menu/<int:item_id>/toggle")
@login_required
@admin_required
def toggle_menu(item_id):
    with db() as c:
        c.execute("UPDATE menu SET available=1-available WHERE id=?",(item_id,))
    return redirect(url_for("admin"))

@app.post("/admin/menu/<int:item_id>/delete")
@login_required
@admin_required
def delete_menu(item_id):
    with db() as c:
        c.execute("DELETE FROM menu WHERE id=?",(item_id,))
    flash("Menu item deleted.","success")
    return redirect(url_for("admin"))

@app.post("/admin/order/<int:order_id>/status")
@login_required
@admin_required
def update_status(order_id):
    status=request.form.get("status")
    if status not in ("Received","Cooking","On the way","Delivered"):
        abort(400)
    with db() as c: c.execute("UPDATE orders SET status=? WHERE id=?",(status,order_id))
    return redirect(url_for("admin"))

@app.get("/admin/export.csv")
@login_required
@admin_required
def export_csv():
    output=io.StringIO(); writer=csv.writer(output)
    writer.writerow(["Order ID","Customer","Phone","Email","Address","Subtotal","GST","Discount","Total","Payment","Status","Date"])
    with db() as c:
        rows=c.execute("SELECT id,customer_name,phone,email,delivery_address,subtotal,gst,discount,total,payment_method,status,created_at FROM orders ORDER BY id").fetchall()
    writer.writerows([tuple(r) for r in rows])
    response=make_response("\\ufeff"+output.getvalue())
    response.headers["Content-Type"]="text/csv; charset=utf-8"
    response.headers["Content-Disposition"]="attachment; filename=globe_table_orders.csv"
    return response

@app.get("/health")
def health():
    return jsonify(status="ok",application="Globe Table",database="SQLite")

@app.errorhandler(403)
def forbidden(_): return render_template("error.html",code=403,message="Admin access only."),403
@app.errorhandler(404)
def not_found(_): return render_template("error.html",code=404,message="The requested page or order was not found."),404

init_db()
if __name__ == "__main__":
    app.run(host="127.0.0.1",port=5000,debug=True)
