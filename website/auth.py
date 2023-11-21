# Standard library imports
from functools import wraps

# Related third party imports
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
import paypalrestsdk
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Local application/library specific imports
from . import db
from .models import Cart, Product, User

paypal_client_id = "ATNxeyrcueUk-PfCIq2BFb4Ky8u0Jui6E96nON3-RyEQqw4o2bU-ltr0UxXxXBayyYCg9nPTJZo_JNNi"
paypal_client_secret = "EJ6NGGXgN-dwwTuIhLxqEHo3eS8y-JMSzsK5hgI7GkljBy9uM65pkeYsQwYNWFt2J9seyQunTPeFs-ku"

auth = Blueprint("auth", __name__)

paypalrestsdk.configure({
    "mode": "sandbox",
    "client_id": paypal_client_id,
    "client_secret": paypal_client_secret
})


def admin_id_required(f):

  @wraps(f)
  def decorated_function(*args, **kwargs):
    user = current_user
    if not user:
      flash("No tan rapido vaquero.", "danger")
      return redirect(url_for("auth.login"))

    expected_user_id = 1
    if user.id != expected_user_id:
      flash("Nu-uh.", "danger")
      return redirect(url_for("views.home"))

    return f(*args, **kwargs)

  return decorated_function


@auth.route("/login", methods=["GET", "POST"])
def login():
  nobars = True
  if request.method == "POST":
    email = request.form.get("email")
    password = request.form.get("password")

    user = User.query.filter_by(email=email).first()
    if user:
      if password:
        if check_password_hash(user.password, password):
          login_user(user, remember=True)
          flash(f"Bienvenid@, {user.username}!", category="success")
          return redirect(url_for("views.home"))
        else:
          flash("Contraseña incorrecta.", category="danger")
    else:
      flash("Usuario no existe.", category="danger")

  return render_template("login.html", user=current_user, nobars=nobars)


@auth.route("/logout")
@login_required
def logout():
  logout_user()
  flash("Te extrañaremos!", category="success")
  return redirect(url_for("views.home"))


@auth.route("/sign_up", methods=["GET", "POST"])
def sign_up():
  nobars = True
  if request.method == "POST":
    email = request.form.get("email")
    username = request.form.get("username")
    password1 = request.form.get("password1")
    password2 = request.form.get("password2")

    user = User.query.filter_by(email=email).first()

    if user:
      flash("El correo electronico ya esta registrado.", category="danger")
    elif len(username) < 3:
      flash("Usuario invalido.", category="danger")
    elif len(email) < 10:
      flash("El correo electronico es invalido.", category="danger")
    elif len(password1) < 4:
      flash("La contraseña debe contener almenos 4 caracteres.",
            category="danger")
    elif password1 != password2:
      flash("Las contraseñas no coinciden.", category="danger")
    else:
      new_user = User(
          email=email,
          username=username,
          password=generate_password_hash(password1,
                                          method="scrypt",
                                          salt_length=16),
      )
      db.session.add(new_user)
      db.session.commit()

      user = User.query.filter_by(email=email).first()

      login_user(user, remember=True)
      flash("Cuenta creada exitosamente!", category="success")
      return redirect(url_for("views.home"))

  return render_template("sign_up.html", user=current_user, nobars=nobars)


@auth.route("/change_password", methods=["GET", "POST"])
def change_password():
  nobars = True
  if request.method == "POST":
    email = request.form.get("email")
    password1 = request.form.get("password1")
    password2 = request.form.get("password2")

    if not email or not password1 or not password2:
      flash("Por favor, complete todos los campos.", "danger")
      return render_template("change_password.html",
                             nobars=nobars,
                             user=current_user)

    user = User.query.filter_by(email=email).first()
    if not user:
      flash("No se encontró ningún usuario con ese correo electrónico.",
            "danger")
      return render_template("change_password.html",
                             nobars=nobars,
                             user=current_user)

    if password1 != password2:
      flash("Las contraseñas no coinciden. Inténtalo de nuevo.", "danger")
      return render_template("change_password.html",
                             nobars=nobars,
                             user=current_user)

    password = generate_password_hash(password1,
                                      method="scrypt",
                                      salt_length=16)
    user.password = password
    db.session.commit()

    flash(
        "Contraseña cambiada exitosamente. Inicia sesión con tu nueva contraseña.",
        "success",
    )
    return redirect(url_for("auth.login"))

  return render_template("change_password.html",
                         nobars=nobars,
                         user=current_user)


@auth.route('/process_payment', methods=['POST'])
def process_payment():
  payment_method = request.form.get('payment_method')
  total_price = request.form.get('total_price')
  if payment_method == 'paypal':
    return redirect(url_for('auth.paypal_checkout', total_price=total_price))
  if payment_method == 'email':
    return redirect(url_for('auth.email_checkout', total_price=total_price))
  if payment_method == 'whatsapp':
    return redirect(url_for('auth.whatsapp_checkout', total_price=total_price))
  else:
    flash("Algo salio mal :(", "danger")
    return redirect(url_for("views.cart"))


@auth.route("/paypal_checkout/<total_price>")
@login_required
def paypal_checkout(total_price):
  cart_items = db.session.query(
      Cart,
      Product).join(Product).filter(Cart.user_id == current_user.id).all()

  item_descriptions = [
      f"{cart_item.Cart.quantity} {cart_item.Product.product}"
      for cart_item in cart_items
  ]

  transaction_description = ", ".join(item_descriptions)
  transaction_amount = float(total_price)

  payment = paypalrestsdk.Payment({
      "intent":
      "sale",
      "payer": {
          "payment_method": "paypal",
      },
      "transactions": [{
          "amount": {
              "total": transaction_amount,
              "currency": "USD",
          },
          "description": transaction_description,
      }],
      "redirect_urls": {
          "return_url": url_for('auth.success', _external=True),
          "cancel_url": url_for('auth.cancel', _external=True),
      },
  })

  if payment.create():
    try:
      for link in payment.links:
        if link.rel == "approval_url":          
          return redirect(link.href)

      flash("No approval URL found.", "danger")
    except Exception as e:
      db.session.rollback()
      flash(str(e), "danger")

    return redirect(url_for('views.cart'))
  else:
    flash("Payment creation failed", "danger")
    return redirect(url_for('views.home'))
  

@auth.route("/success")
def success():
  cart_items = db.session.query(
      Cart,
      Product).join(Product).filter(Cart.user_id == current_user.id).all()

  for cart_item in cart_items:
    product = cart_item.Product
    product.quantity -= cart_item.Cart.quantity
    
  Cart.query.filter_by(user_id=current_user.id).delete()
  db.session.commit()

  flash("¡Gracias por preferirnos!", "success")
  return redirect(url_for("views.cart"))


@auth.route("/cancel")
def cancel():
  return redirect(url_for("views.cart"))


@auth.route('/email_checkout/<total_price>')
def email_checkout(total_price):
  user = User.query.filter_by(id=current_user.id).first()
  client_email = user.email
  my_email = "donfernandogm@gmail.com"
  subject = f"Pedido para {user.username}"
  cart_items = db.session.query(
      Cart,
      Product).join(Product).filter(Cart.user_id == current_user.id).all()

  item_descriptions = [
      f"{cart_item.Cart.quantity} {cart_item.Product.product}"
      for cart_item in cart_items
  ]

  transaction_description = ", ".join(item_descriptions)
  transaction_amount = float(total_price)

  message = f"Se ha realizado una compra con los siguientes detalles: Descripción: {transaction_description}, Monto: ${transaction_amount:.2f}. Por favor, revise los detalles de la transacción."

  msg = MIMEMultipart('alternative')
  msg['Subject'] = subject
  msg['From'] = my_email
  msg['To'] = client_email

  part1 = MIMEText(message, 'plain')

  msg.attach(part1)

  try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('donfernandogm@gmail.com', 'zuzb xxbp pvum yzeb')

    server.sendmail(client_email, my_email, msg.as_string())
    server.quit()

    Cart.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    flash("Tu pedido ha sido enviado correctamente! Estaremos en contacto.", "success")
    return redirect(url_for('views.cart'))
  except Exception as e:
    flash(f"Error al enviar el correo. Error: {str(e)}", "danger")
    return redirect(url_for('views.cart'))


@auth.route('/whatsapp_checkout/<total_price>')
def whatsapp_checkout(total_price):
    cart_items = db.session.query(
      Cart,
      Product).join(Product).filter(Cart.user_id == current_user.id).all()    
    item_descriptions = [
      f"{cart_item.Cart.quantity} {cart_item.Product.product}"
      for cart_item in cart_items
    ]
    transaction_description = ", ".join(item_descriptions)
    transaction_amount = float(total_price)

    whatsapp_number = '+584164223250'
    whatsapp_message = "Hola, me gustaría poner una orden de " + transaction_description + ". El total sería: " + str(transaction_amount)
    whatsapp_url = f"https://wa.me/{whatsapp_number}?text={whatsapp_message}"

    Cart.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    return redirect(whatsapp_url)

