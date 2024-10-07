from flask import Flask, request, redirect, jsonify, session, make_response
from flask.templating import render_template
from flask_sqlalchemy import SQLAlchemy
import mysql.connector
from datetime import datetime
import enum

app = Flask(__name__)
app.debug = True

app.config.from_mapping(
    SECRET_KEY="mysecretkey",
    SQLALCHEMY_DATABASE_URI="mysql+mysqlconnector://intern2:1234@172.20.48.1:3306/invoice_page_db",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={
        "pool_recycle": 899,  # Set pool recycle time (in seconds)
        "isolation_level": "READ COMMITTED",  # Set transaction isolation level
    }
)
db: SQLAlchemy = SQLAlchemy(app)
#db.init_app(app)

class StatusEnum(enum.Enum):
    PAID = "paid"
    UNPAID = "unpaid"

# Models
class Invoices(db.Model):
    __tablename__ = "invoices"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(20), unique=False, nullable=False)
    company_name = db.Column(db.String(20), nullable=False)
    due_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status=db.Column(db.Enum(StatusEnum), default=StatusEnum.UNPAID, nullable=True)
    url=db.Column(db.String(255), nullable=True)

    # repr method represents how one object of this datatable will look like
    def __repr__(self):
        return f"<Invoice {self.company_name}, Amount: {self.amount}, Status: {self.status}>"

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    # Number of profiles to show per page
    per_page = 10
    # Use SQLAlchemy's paginate method to get profiles for the current page
    invoices = Invoices.query.paginate(page=page, per_page=per_page)
    return render_template('index.html', invoices=invoices)

@app.route('/invoices', methods=['GET'])
def add_invoices():
    return render_template('add_invoice.html')

@app.route('/invoices', methods=['POST'])
def create_invoice():
    amount = request.form.get('amount')
    currency = request.form.get('currency')
    company_name = request.form.get('company_name')
    due_date = request.form.get('due_date')
    status = request.form.get('status')
    url = request.form.get('url')
    if amount is not None and currency != '' and company_name != '' and due_date != '' and status == 'paid' or status == 'unpaid':
        i = Invoices(amount=amount, currency=currency, company_name=company_name, due_date=due_date, status=status, url=url)
        db.session.add(i)
        db.session.commit()
        return redirect('/')
    else:
        return redirect('/')

@app.before_request
def override_method():
    # Check if the request is POST and has the `_method` hidden field.
    if request.method == 'POST' and '_method' in request.form:
        method = request.form['_method']
        if method in ['PUT', 'DELETE']:
            request.environ['REQUEST_METHOD'] = method
@app.route('/invoices/<int:id>', methods=['POST', 'DELETE'])
def delete_invoice(id):
    # Deletes the data on the basis of unique id and redirects to home page
    data = Invoices.query.get(id)
    if data:
        db.session.delete(data)
        db.session.commit()
        return redirect('/')
    else:
        return "Invoice not found", 404

if __name__ == '__main__':
    with app.app_context():  # Ensure the app context is available
        print("Creating database and tables...")
        db.create_all()
        print("Database and tables created successfully!")
    app.run()