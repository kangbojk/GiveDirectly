import datetime
from flask import Flask, request, jsonify
import os
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import re

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'db.sqlite3')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)


class UserModel(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)

    loans = db.relationship('LoanModel',
                            backref=db.backref('user', lazy=True))

    def __init__(self, email):
        self.email = email

    def __repr__(self):
        return f'User(id: {self.id:>2}, email: {self.email:^20})'


class BookModel(db.Model):
    __tablename__ = 'book'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), default="", nullable=False, unique=True)

    borrower = db.relationship('LoanModel',
                               backref=db.backref('book', lazy=True))

    def __init__(self, title):
        self.title = title

    def __repr__(self):
        return f'Book(id: ${self.id:>2}, title: ${self.title:^20})'


class LoanModel(db.Model):
    __tablename__ = 'lending'
    id = db.Column(db.Integer, primary_key=True)
    borrower_id = db.Column(
        db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey(
        'book.id'), nullable=False)

    loan_date = db.Column(db.DateTime, nullable=False,
                          default=datetime.datetime.now)
    return_date = db.Column(db.DateTime, nullable=True)

    def __init__(self, borrower_id, book_id):
        self.borrower_id = borrower_id
        self.book_id = book_id

    def __repr__(self):
        # we might print the LoanModel before we commit, so id might be None
        return 'Loan(%s, borrower=%s,book=%s)' % (self.id, self.borrower_id, self.book_id)


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel


class BookSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = BookModel


class LendingSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = LoanModel
        include_fk = True


user_schema = UserSchema()
user_schemas = UserSchema(many=True)

loan_schema = LendingSchema()
loan_schemas = LendingSchema(many=True)

book_schema = BookSchema()
book_schemas = BookSchema(many=True)


@app.before_first_request
def create_tables():
    db.create_all()


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/add_books")
def add_books():

    b1 = BookModel("Harry Potter")
    b2 = BookModel("Art War")
    b3 = BookModel("Game")
    b4 = BookModel("House")
    books = [b1, b2, b3, b4]

    db.session.add_all(books)
    db.session.commit()
    return 'Finish adding books'


@app.route("/books")
def get_books():
    all_books = BookModel.query.all()
    result = book_schemas.dump(all_books)

    return jsonify(result)


@app.route("/users")
def get_users():
    all_users = UserModel.query.all()
    result = user_schemas.dump(all_users)

    return jsonify(result)


@app.route("/request")
def get_loans():
    all_loans = LoanModel.query.all()
    if all_loans:
        result = loan_schemas.dump(all_loans)
        return jsonify(result)
    else:
        return jsonify({
            'message': "No data"
        })


@app.route("/request/<id>")
def get_loan_with_loan_id(id):
    loan = LoanModel.query.get(id)
    result = loan_schema.dump(loan)
    return jsonify(result)


@app.route("/request", methods=['POST'])
def request_book():
    email = request.json['email']
    title = request.json['title']

    if not EMAIL_REGEX.match(email):
        return jsonify({
            'message': "Please enter email in correct format"
        })

    user = UserModel.query.filter_by(email=email).first()
    if not user:
        new_user = UserModel(email)
        db.session.add(new_user)
        db.session.commit()
        user = new_user

    book = BookModel.query.filter_by(title=title).first()

    if not book:
        return jsonify({
            'message': "No such book"
        })

    # ideally we could use .first(), just to make sure no books are being borrowed twice before return
    Loans = LoanModel.query.join(BookModel, BookModel.id == LoanModel.book_id).filter(
        BookModel.title == title).filter(LoanModel.return_date == None).all()

    if Loans:
        return jsonify({
            'id': Loans[0].id,
            'available': False,
            'title': title,
            'timestamp': Loans[0].loan_date
        })

    new_loan = LoanModel(user.id, book.id)
    db.session.add(new_loan)
    db.session.commit()

    return jsonify({
        'id': new_loan.id,
        'available': True,
        'title': book.title,
        'timestamp': new_loan.loan_date
    })


# alternatively we could use another POST end point to set return date for loan
@app.route("/request/<id>", methods=['DELETE'])
def remove_loan(id):
    loan = LoanModel.query.get(id)
    if loan:
        db.session.delete(loan)
        db.session.commit()
        result = loan_schema.dump(loan)
        return f"Successfully delete {result}\n"
    else:
        return f"No item to delete\n"


if __name__ == '__main__':
    db.init_app(app)
    ma.init_app(app)
    app.run(port=5000, debug=True)
