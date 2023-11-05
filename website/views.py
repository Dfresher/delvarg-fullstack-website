from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import User, Product, Cart, Heart, Tags
from .auth import admin_id_required
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from . import db
import base64

views = Blueprint("views", __name__)


@views.route("/")
def home():
    products = Product.query.all()
    products_with_images = []
    cart_count=0
    heart_count=0

    if current_user.is_authenticated:
        user_id = current_user.id
        product_count = (
            db.session.query(func.sum(Cart.quantity))
            .filter_by(user_id=user_id)
            .scalar()
        )
        if product_count is not None:
            cart_count = product_count
        else:
            cart_count = 0
        
        liked_product_count = (
        db.session.query(func.count(Heart.id))
        .filter(Heart.user_id == user_id, Heart.heart_state == "filled")
        .scalar()
        )
        if liked_product_count is not None:
            heart_count = liked_product_count
        else:
            heart_count = 0

    for product in products:
        if product.image:
            b64_image = base64.b64encode(product.image).decode("utf-8")
            product_copy = product.__class__()
            product_copy.__dict__.update(product.__dict__)
            product_copy.image = b64_image
            product_copy.new_price = "{:.2f}".format(
                float(product.price * (1 - product.deal / 100))
            )

            if current_user.is_authenticated:
                heart_info = Heart.query.filter_by(
                    user_id=user_id, product_id=product.id
                ).first()
                if heart_info:
                    product_copy.heart_info = heart_info
                else:
                    product_copy.heart_info = None

            products_with_images.append(product_copy)
        else:
            products_with_images.append(product)

    return render_template(
        "home.html",
        user=current_user,
        products=products_with_images,
        cart_count=cart_count,
        heart_count=heart_count
    )


@views.route("/add_to_cart", methods=["POST"])
@login_required
def add_to_cart():
    product_id = request.form.get("product_id")
    user_id = current_user.id
    product_quantity = int(request.form.get("product_quantity"))

    existing_cart_entry = Cart.query.filter_by(
        user_id=user_id, product_id=product_id
    ).first()
    if existing_cart_entry:
        existing_cart_entry.quantity += product_quantity
    else:
        cart_entry = Cart(
            quantity=product_quantity, user_id=user_id, product_id=product_id
        )
        db.session.add(cart_entry)

    db.session.commit()

    flash("Producto añadido al carrito!", "success")
    return redirect(url_for("views.home"))


@views.route("/delete_from_cart", methods=["POST"])
@login_required
def delete_from_cart():
    user_id = current_user.id
    product_id = int(request.form["product_id_del"])
    quantity_to_delete = int(request.form["product_quantity_del"])

    cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

    if cart_item:
        new_quantity = cart_item.quantity - quantity_to_delete

        if new_quantity > 0:
            cart_item.quantity = new_quantity
            db.session.commit()
        else:
            db.session.delete(cart_item)
            db.session.commit()

    flash("Producto eliminado del carrito", "success")
    return redirect(url_for("views.cart"))


@views.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    nobars = True
    user_id = current_user.id
    total_price = 0

    if request.method == "POST":
        product_id = request.form.get("product_id")
        product_quantity = int(request.form.get("product_quantity"))

        existing_cart_entry = Cart.query.filter_by(
            user_id=user_id, product_id=product_id
        ).first()

        if existing_cart_entry:
            existing_cart_entry.quantity += product_quantity
        else:
            cart_entry = Cart(
                quantity=product_quantity, user_id=user_id, product_id=product_id
            )
            db.session.add(cart_entry)

        db.session.commit()
        flash("Producto añadido al carrito!", "success")
        return redirect(url_for("views.cart", nobars=nobars))

    total_quantity = (
        db.session.query(func.sum(Cart.quantity)).filter_by(user_id=user_id).scalar()
        or 0
    )
    
    liked_product_count = (
        db.session.query(func.count(Heart.id))
        .filter(Heart.user_id == user_id, Heart.heart_state == "filled")
        .scalar()
        )
    
    if liked_product_count is not None:
        heart_count = liked_product_count
    else:
        heart_count = 0

    cart_entries = Cart.query.filter_by(user_id=user_id).all()
    product_ids = [entry.product_id for entry in cart_entries]

    products = Product.query.filter(Product.id.in_(product_ids)).all()

    products_with_quantities = []

    for product, cart_entry in zip(products, cart_entries):
        if cart_entry.quantity > 0:
            product_copy = product.__class__()
            product_copy.__dict__.update(product.__dict__)
            product_copy.quantity = cart_entry.quantity

            if product_copy.image:
                b64_image = base64.b64encode(product_copy.image).decode("utf-8")
                product_copy.image = b64_image

            products_with_quantities.append(product_copy)

            item_price = product.price * cart_entry.quantity
            total_price += item_price

    return render_template(
        "cart.html",
        user=current_user,
        products=products_with_quantities,
        cart_count=total_quantity,
        heart_count=heart_count,
        total_price=total_price,
        nobars=nobars,
    )


@views.route("/toggle_heart/<int:product_id>", methods=["POST"])
@login_required
def toggle_heart(product_id):
    user = current_user
    product = Product.query.get(product_id)
    heart = Heart.query.filter_by(user_id=user.id, product_id=product.id).first()

    if heart:
        if heart.heart_state == "filled":
            heart.heart_state = "cracked"
        elif heart.heart_state == "cracked":
            db.session.delete(heart)
            db.session.commit()
            return redirect(request.referrer)
        else:
            heart.heart_state = "filled"
    else:
        heart = Heart(user_id=user.id, product_id=product.id, heart_state="filled")

    db.session.add(heart)
    db.session.commit()

    return redirect(request.referrer)


@views.route("/heart", methods=["GET", "POST"])
@login_required
def heart():
    nobars = True
    user_id = current_user.id
    cart_count = Cart.query.with_entities(func.sum(Cart.quantity)).filter_by(user_id=user_id).scalar() or 0
    heart_count = Heart.query.filter(Heart.user_id == user_id, Heart.heart_state == "filled").count()

    if request.method == "POST":
        product_id = request.form.get("product_id")
        product = Product.query.get(product_id)
        heart = Heart.query.filter_by(user_id=user_id, product_id=product_id).first()

        if heart:
            if heart.heart_state == "filled":
                heart.heart_state = "cracked"
            elif heart.heart_state == "cracked":
                heart.heart_state = "empty"
            else:
                heart.heart_state = "filled"
        else:
            heart = Heart(user_id=user_id, product_id=product_id, heart_state="filled")

        db.session.add(heart)
        db.session.commit()

        return redirect(url_for("views.home"))

    liked_products = (
        Product.query
        .join(Heart, Product.id == Heart.product_id)
        .filter(Heart.user_id == user_id, Heart.heart_state == "filled")
        .all()
    )


    products_with_images = []
    for product in liked_products:
        if product.image:
            b64_image = base64.b64encode(product.image).decode("utf-8")
            product_copy = product.__class__()
            product_copy.__dict__.update(product.__dict__)
            product_copy.image = b64_image
            product_copy.new_price = "{:.2f}".format(
                float(product.price * (1 - product.deal / 100))
            )

            heart_info = Heart.query.filter_by(
                    user_id=user_id, product_id=product.id
                ).first()
            if heart_info:
                product_copy.heart_info = heart_info
            else:
                product_copy.heart_info = None

            products_with_images.append(product_copy)
        else:
            products_with_images.append(product)

    return render_template(
        "heart.html",
        user=current_user,
        products=products_with_images,
        cart_count=cart_count,
        heart_count=heart_count,
        nobars=nobars,
    )


@views.route("/faq", methods=["GET", "POST"])
def faq():
    nobars = True
    return render_template("faq.html", user=current_user, nobars=nobars)


@views.route("/admin", methods=["GET"])
@login_required
@admin_id_required
def admin():
    nobars = True
    return render_template("admin.html", user=current_user, nobars=nobars)


@views.route("/add_product", methods=["GET", "POST"])
@login_required
@admin_id_required
def add_product():
    nobars = True

    if request.method == "POST":
        product_image = request.files.get("product_image")
        product_name = request.form.get("product_name")
        product_filter = request.form.get("product_filter")
        product_price = request.form.get("product_price")
        product_deal = request.form.get("product_deal")

        if not product_image:
            flash("Selecciona una imagen.", "danger")
        elif len(product_name) < 2:
            flash("El nombre del producto es muy corto.", "danger")
        elif len(product_filter) < 2:
            flash("Filtro inválido.", "danger")
        elif not product_deal.isdigit():
            flash("Descuento inválido.", "danger")
        elif product_price:
            try:
                product_price = "{:.2f}".format(float(product_price))
            except ValueError:
                flash("Precio inválido.", "danger")
        else:
            flash("Precio inválido.", "danger")

        if not any(
            [product_name, product_filter, product_price, product_deal, product_image]
        ):
            flash("Ningún cambio detectado.", "info")
        else:
            try:
                if product_image:
                    image_data = product_image.read()
                    new_product = Product(
                        product=product_name,
                        filter=product_filter,
                        price=product_price,
                        deal=product_deal,
                        image=image_data,
                    )
                    db.session.add(new_product)
                    db.session.commit()
                    flash("Producto agregado correctamente!", category="success")
            except Exception as e:
                flash("Error al agregar el producto: " + str(e), category="danger")

        return redirect(url_for("views.add_product"))

    else:
        return render_template("add_product.html", user=current_user, nobars=nobars)


@views.route("/edit_product", methods=["GET", "POST"])
@login_required
@admin_id_required
def edit_product():
    nobars = True
    if request.method == "POST":
        product_name = request.form["product_name"]
        product_filter = request.form["product_filter"]
        product_price = request.form["product_price"]
        product_deal = request.form["product_deal"]
        product_id = request.form["product_id"]

        if "product_image" in request.files:
            product_image = request.files["product_image"]
        else:
            product_image = None

        if len(product_name) < 2:
            flash("El nombre del producto es muy corto.", "danger")
            return redirect(url_for("views.edit_product"))
        elif len(product_filter) < 2:
            flash("Filtro invalido.", "danger")
            return redirect(url_for("views.edit_product"))
        elif not product_deal.isdigit():
            flash("Descuento invalido.", "danger")
            return redirect(url_for("views.edit_product"))
        elif product_price:
            try:
                product_price = "{:.2f}".format(float(product_price))
            except ValueError:
                flash("Precio inválido.", "danger")
                return redirect(url_for("views.edit_product"))
        else:
            flash("Precio inválido.", "danger")
            return redirect(url_for("views.edit_product"))

        try:
            existing_product = Product.query.get(product_id)

            if existing_product:
                if product_image:
                    existing_product.product = product_name
                    existing_product.filter = product_filter
                    existing_product.price = product_price
                    existing_product.deal = product_deal
                    existing_product.image = product_image.read()
                else:
                    existing_product.product = product_name
                    existing_product.filter = product_filter
                    existing_product.price = product_price
                    existing_product.deal = product_deal

                db.session.commit()
                flash("Producto editado correctamente!", category="success")
            else:
                flash("Producto no encontrado", "danger")

        except Exception as e:
            flash("Error al editar el producto: " + str(e), "danger")
        return redirect(url_for("views.edit_product"))

    else:
        products = Product.query.all()
        products_with_images = []
        cart_count = 0

        if current_user.is_authenticated:
            user_id = current_user.id
            total_quantity = (
                db.session.query(func.sum(Cart.quantity))
                .filter_by(user_id=user_id)
                .scalar()
            )
            if total_quantity is not None:
                cart_count = total_quantity
            else:
                cart_count = 0

        for product in products:
            if product.image:
                b64_image = base64.b64encode(product.image).decode("utf-8")
                product_copy = product.__class__()
                product_copy.__dict__.update(product.__dict__)
                product_copy.image = b64_image

                products_with_images.append(product_copy)
            else:
                products_with_images.append(product)

        return render_template(
            "edit_product.html",
            user=current_user,
            products=products_with_images,
            cart_count=cart_count,
            nobars=nobars,
        )


@views.route("/delete_product", methods=["POST"])
@login_required
@admin_id_required
def delete_product():
    product_id = request.form.get("product_id")

    product = Product.query.get(product_id)

    if product:
        Cart.query.filter_by(product_id=product_id).delete()
        Heart.query.filter_by(product_id=product_id).delete()
        Tags.query.filter_by(product_id=product_id).delete()

        db.session.delete(product)
        db.session.commit()
        flash("Producto eliminado correctamente", "success")
    else:
        flash("Producto no encontrado", "danger")

    return redirect(request.referrer)


@views.route("/manage_users", methods=["GET", "POST"])
@login_required
@admin_id_required
def manage_users():
    nobars = True
    try:
        users = User.query.all()
    except SQLAlchemyError as e:
        print("Database error:", str(e))
        users = []

    if request.method == "POST":
        user_id = request.form.get("user_id")
        if user_id:
            try:
                user = User.query.get(user_id)
                if user:
                    db.session.delete(user)
                    db.session.commit()

                else:
                    pass
            except SQLAlchemyError as e:
                print("Database error:", str(e))

    else:
        return render_template(
            "manage_users.html", users=users, user=current_user, nobars=nobars
        )
