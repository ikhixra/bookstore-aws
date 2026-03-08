from flask import Flask, render_template, request, redirect, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "secret123"

# MySQL Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="bookstore"
)

cursor = db.cursor(dictionary=True, buffered=True)



# HOME PAGE (SHOW BOOKS)
@app.route("/")
def home():

    search = request.args.get("search")

    if search:
        sql = "SELECT * FROM books WHERE title LIKE %s"
        cursor.execute(sql, ("%" + search + "%",))
    else:
        cursor.execute("SELECT * FROM books")

    books = cursor.fetchall()

    cart_count = 0

    if "user_id" in session:
        cursor.execute(
            "SELECT COUNT(*) AS count FROM cart WHERE user_id=%s",
            (session["user_id"],)
        )
        cart_count = cursor.fetchone()["count"]

    return render_template("index.html", books=books, cart_count=cart_count)

    


# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        sql = "INSERT INTO users (name,email,password) VALUES (%s,%s,%s)"
        cursor.execute(sql,(name,email,password))
        db.commit()

        return redirect("/login")

    return render_template("register.html")


# LOGIN
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        sql = "SELECT * FROM users WHERE email=%s AND password=%s"
        cursor.execute(sql,(email,password))
        user = cursor.fetchone()

        if user:

            session["user_id"] = user["id"]
            session["name"] = user["name"]

            return redirect("/")

        else:
            return "Invalid Email or Password"

    return render_template("login.html")


# LOGOUT
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ADD TO CART
@app.route("/add_to_cart/<int:book_id>")
def add_to_cart(book_id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    # check if item already in cart
    sql = "SELECT * FROM cart WHERE user_id=%s AND book_id=%s"
    cursor.execute(sql,(user_id,book_id))
    item = cursor.fetchone()

    if item:
        sql = "UPDATE cart SET quantity = quantity + 1 WHERE id=%s"
        cursor.execute(sql,(item["id"],))
    else:
        sql = "INSERT INTO cart (user_id, book_id, quantity) VALUES (%s,%s,1)"
        cursor.execute(sql,(user_id,book_id))

    db.commit()

    return redirect("/cart")
# VIEW CART
# VIEW CART
@app.route("/cart")
def cart():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    sql = """
    SELECT cart.id, books.title, books.price, books.image, cart.quantity
    FROM cart
    JOIN books ON cart.book_id = books.id
    WHERE cart.user_id = %s
    """

    cursor.execute(sql,(user_id,))
    cart_items = cursor.fetchall()

    total = 0
    for item in cart_items:
        total += item["price"] * item["quantity"]

    return render_template("cart.html", items=cart_items, total=total)
@app.route("/remove/<int:cart_id>")
def remove(cart_id):

    if "user_id" not in session:
        return redirect("/login")

    sql = "DELETE FROM cart WHERE id=%s"
    cursor.execute(sql,(cart_id,))
    db.commit()

    return redirect("/cart")
@app.route("/checkout")
def checkout():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    # get cart items
    sql = """
    SELECT cart.book_id, cart.quantity, books.price
    FROM cart
    JOIN books ON cart.book_id = books.id
    WHERE cart.user_id = %s
    """

    cursor.execute(sql,(user_id,))
    items = cursor.fetchall()

    total = 0
    for item in items:
        total += item["price"] * item["quantity"]

    # create order
    sql = "INSERT INTO orders(user_id,total) VALUES(%s,%s)"
    cursor.execute(sql,(user_id,total))
    db.commit()

    order_id = cursor.lastrowid

    # insert order items
    for item in items:
        sql = """
        INSERT INTO order_items(order_id,book_id,quantity,price)
        VALUES(%s,%s,%s,%s)
        """
        cursor.execute(sql,(order_id,item["book_id"],item["quantity"],item["price"]))

    db.commit()

    # clear cart
    sql = "DELETE FROM cart WHERE user_id=%s"
    cursor.execute(sql,(user_id,))
    db.commit()

    return render_template("order_success.html")
@app.route("/orders")
def orders():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    sql = """
    SELECT orders.id, orders.total, orders.created_at
    FROM orders
    WHERE user_id = %s
    ORDER BY created_at DESC
    """

    cursor.execute(sql,(user_id,))
    orders = cursor.fetchall()

    return render_template("orders.html", orders=orders)
if __name__ == "__main__":
    app.run(debug=True)