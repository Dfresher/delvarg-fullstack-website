from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    username = db.Column(db.String(150))
    password = db.Column(db.String(150))
    cart_info = db.relationship("Cart")
    heart_info = db.relationship("Heart")


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(150))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    deal = db.Column(db.Integer)
    image = db.Column(db.LargeBinary)
    tags_info = db.relationship(
        "Tags", secondary="product_tags", backref="products", lazy="joined"
    )


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))


class Heart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    heart_state = db.Column(db.String(20), default="empty")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))


class Tags(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.String(150))
    parent_tag_id = db.Column(db.Integer, db.ForeignKey("tags.id"))
    parent_tag = db.relationship(
        "Tags", remote_side=[id], backref=db.backref("child_tags", lazy="joined")
    )


class ProductTags(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    tag_id = db.Column(db.Integer, db.ForeignKey("tags.id"))
