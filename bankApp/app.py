from flask import (
    Flask,
    g,
    redirect,
    render_template,
    request,
    make_response,
    session,
    url_for, 
    abort,
    Response
)
from flask_sqlalchemy import SQLAlchemy, BaseQuery
from datetime import datetime
import json
import io
import xlwt
import random
import string
import pdfkit
try:
    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
except Exception as e:
    print("OSError on line number 22: No wkhtmltopdf executable found: If this file exists please check that this process can read it. Otherwise please install wkhtmltopdf - https://github.com/JazzCore/python-pdfkit/wiki/Installing-wkhtmltopdf")


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///customer.db'
app.secret_key = 'SecretKey'

class CustomBaseQuery(BaseQuery):
    def get_or_404(self, ident):
        model_class_name = ''
        try:
            model_class_name = self._mapper_zero().class_.__name__
        except Exception as e:
            print(e)

        rv = self.get(ident)
        if not rv:
            error_message = json.dumps({'message': model_class_name + ' ' + str(ident) + ' not found'})
            Response(error_message, 404)
        return rv


db = SQLAlchemy(app, query_class=CustomBaseQuery)


@app.before_request
def before_request():
    g.user = None

    if 'user_id' in session:
        user = [x for x in users if x.id == session['user_id']][0]
        g.user = user




class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return "Customer name: " + self.name


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ssnid = db.Column(db.Integer, nullable=True)
    account_type = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    message = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return "SSNID name: " + str(self.ssnid)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, nullable=True)
    ssnid = db.Column(db.Integer, nullable=True)
    account_type = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    message = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return "SSNID name: " + str(self.id)


class Cashier():
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __repr__(self):
        return "User name: " + self.username

users = []
users.append(Cashier(id=1, username='john wick', password='JohnWick@123'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('user_id', None)
        username = request.form['username']
        password = request.form['password']
        user = [x for x in users if x.username == username]
        if (user):
            user = user[0]
        else:
            user = None
        if user and user.password == password:
            session['user_id'] = user.id
            return redirect('/home')
        else:
            return redirect('/login')
    else:
        return render_template('login.html')





@app.route('/home')
def home():
    if not g.user:
        return redirect('/login')
    return render_template('home.html')
    



@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')


@app.route('/create_customer', methods=['GET', 'POST'])
def create_customer():
    if not g.user:
        return redirect('/login')
    customer_id = request.form['ssnid']
    customer_name = request.form['name']
    customer_age = request.form['age']
    customer_address = request.form['address']
    customer_city = request.form['city']
    customer_state = request.form['state']
    if (len(customer_id) != 8):
        return render_template('createcustomer.html', error_for_id="The length of the customer SSNID should be 8 digits.")
    try:
        int(customer_age)
    except Exception as e:
        return render_template('createcustomer.html', error_for_age="The age should be number.")
    new_customer = Customer(id=customer_id, name=customer_name, age=customer_age, address=customer_address, city=customer_city, state=customer_state, message="Customer created successfully", status="Active")
    db.session.add(new_customer)
    db.session.commit()
    return render_template('message.html', message="Customer created successfully and Customer SSNID is "+ customer_id)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    if not g.user:
        return redirect('/login')
    if request.method == 'POST':
        customer_ssnid = request.form['ssnid']
        customer = Customer.query.get_or_404(customer_ssnid)
        if customer:
            return render_template('update.html', customer=customer)
        else:
            err = "Customer with given SSNID is not found."
            return render_template('edit.html', error=err)
    else:
        return render_template('edit.html')


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    if not g.user:
        return redirect('/login')
    if request.method == 'POST':
        customer = Customer.query.get_or_404(id)
        try:
            customer_age = request.form['age']
            int(customer_age)
        except Exception as e:
            return render_template('update.html', error="The age should be a number.", customer=customer)
        customer.name = request.form['name']
        customer.age = request.form['age']
        customer.address = request.form['address']
        customer.message = 'Customer updated successfully'
        customer.date_created = datetime.utcnow()
        db.session.commit()
        return render_template('message.html', message="Customer updated successfully and Customer SSNID is "+ str(customer.id))



@app.route('/createcustomer')
def new_customer():
    if not g.user:
        return redirect('/login')
    return render_template('createcustomer.html')


@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if not g.user:
        return redirect('/login')
    if request.method == 'POST':
        customer_ssnid = request.form['customerssnid']
        customer = Customer.query.get_or_404(customer_ssnid)
        if customer:
            return render_template('deletecustomer.html', customer=customer)
        else:
            err = "Customer with given SSNID is not found."
            return render_template('delete.html', error=err)
    else:
        return render_template('delete.html')



@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete_customer(id):
    if not g.user:
        return redirect('/login')
    if request.method == 'POST':
        customer = Customer.query.get_or_404(id)
        db.session.delete(customer)
        db.session.commit()
        return render_template('message.html', message="Customer deleted successfully and Customer SSNID is "+ str(customer.id))



@app.route('/createaccount', methods=['GET', 'POST'])
def create_account():
    if not g.user:
        return redirect('/login')
    if request.method == 'POST':
        account_id = request.form['id']
        customer_ssnid = request.form['ssnid']
        account_type = request.form['type']
        amount = request.form['amount']
        try:
            account = Account.query.get_or_404(account_id)
            if (account.id == int(account_id)):
                return render_template('/createaccount.html', error="You already have an account on this id "+ str(account_id))
        except Exception as e:
            pass
        try:
            int(amount)
        except Exception as e:
            return render_template('createaccount.html', error_for_amount="The Amount should be number")
        if (len(account_id) != 8):
            return render_template('createaccount.html', error_for_id="The length of the account ID should be of 8 digits.")
        if (len(customer_ssnid) != 8):
            return render_template('createaccount.html', error_for_ssnid="The length of the customer SSNID should be of 8 digits.")
        if (account_type == "savings"):
            if (int(amount) <= 5000):
                return render_template('createaccount.html', error_for_amount_savings="For savings account the minimum amount should be 5000")
        if (account_type == "current"):
            if (int(amount) <= 7000):
                return render_template('createaccount.html', error_for_amount_current="For current account the minimum amount should be 7000") 
        try:
            account = Account.query.filter(Account.ssnid==customer_ssnid,Account.account_type==account_type).all()[0]
            return render_template('/createaccount.html', error="You already have a "+ account_type +" account for customer SSNID "+ str(customer_ssnid)) 
        except Exception as e:
            new_account = Account(id=account_id, ssnid=customer_ssnid, account_type=account_type, amount=amount, message='Account created successfully', status='Active')
            db.session.add(new_account)
            db.session.commit()
            return render_template('message.html', message="Account created successfully and Customer SSNID is "+ str(customer_ssnid))
    else:
        return render_template('createaccount.html')



@app.route("/deleteaccount", methods=['GET', 'POST'])
def deleteaccount():
    if not g.user:
        return redirect('/login')
    if request.method == 'POST':
        customer_ssnid = request.form['customerssnid']
        account_type = request.form['type']
        try:
            account = Account.query.filter(Account.ssnid==customer_ssnid,Account.account_type==account_type).all()[0]
            if account.ssnid == int(customer_ssnid):
                return render_template('deleteacc.html', account=account)
        except Exception as e:
            err = "Ther is no Account with given SSNID " + str(customer_ssnid) + " and given account type " + account_type + "."  
            return render_template('deleteaccount.html', error=err)
    else:
        return render_template('deleteaccount.html')



@app.route('/deleteaccount/<int:ssnid>/<string:account_type>', methods=['GET', 'POST'])
def delete_account(ssnid, account_type):
    if not g.user:
        return redirect('/login')
    if request.method == 'POST':
        account = Account.query.filter(Account.ssnid==ssnid,Account.account_type==account_type).all()[0]
        db.session.delete(account)
        db.session.commit()
        return render_template('message.html', message="Account deleted successfully for Customer SSNID is "+ str(ssnid) + " and account id is "+ str(account.id))



@app.route('/searchcustomer', methods=['GET', 'POST'])
def search_customer():
    if not g.user:
        return redirect('/login')
    if request.method == 'POST':
        customer_id = request.form['ssnid']
        try:
            customer = Customer.query.filter_by(id=customer_id).all()[0]
            return render_template('searchcust.html', customer=customer)
        except Exception as e:
            return render_template('searchcustomer.html', error="No customer has this SSNID "+str(customer_id)+". Enter correct SSNID.")
    else:
        return render_template('searchcustomer.html')



@app.route('/searchaccount', methods=['GET', 'POST'])
def search_account():
    if not g.user:
        return redirect('/login')
    if request.method == 'POST':
        account_id = request.form['id']
        try:
            account = Account.query.filter_by(id=account_id).all()[0]
            return render_template('searchacc.html', account=account)
        except Exception as e:
            return render_template('searchaccount.html', error="No account has this ID "+account_id+". Enter correct Account ID.")
    else:
        return render_template('searchaccount.html')

    
@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if not g.user:
        return redirect('/login')
    if request.method == 'POST':
        customer_ssnid = request.form['customerid']
        account_id = request.form['accountid']
        account_type = request.form['accounttype']
        withdraw_amount = request.form['withdrawamount']
        try:
            account = Account.query.filter(Account.ssnid==customer_ssnid,Account.account_type==account_type).all()[0]
            if account.amount < int(withdraw_amount):
                return render_template('withdraw.html', error="You don't have enough succificent balance in your account.You have only "+str(account.amount)+" amount in your account.")
            elif account.ssnid == int(customer_ssnid) and account.account_type == account_type:
                account.amount = account.amount - int(withdraw_amount)
                account.message = 'Withdraw successfully'
                account.date_created = datetime.utcnow()
                transaction_id = ''.join(random.choices(string.digits, k=8))
                transaction = Transaction(id=transaction_id,account_id=account_id,ssnid=customer_ssnid,account_type=account_type,message="Withdraw",amount=withdraw_amount)
                db.session.add(transaction)
                db.session.commit()
                return render_template('message.html', account=account)
        except Exception as e:
            return render_template('withdraw.html', error="There is no account with this SSNID "+customer_ssnid+" and account id "+account_id+". Enter correct Account ID.")
    else:
        return render_template('withdraw.html')


@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if not g.user:
        return redirect('/login')
    if request.method == 'POST':
        customer_ssnid = request.form['customerid']
        account_id = request.form['accountid']
        account_type = request.form['accounttype']
        withdraw_amount = request.form['depositamount']
        try:
            account = Account.query.filter(Account.ssnid==customer_ssnid,Account.account_type==account_type).all()[0]
            if account.ssnid == int(customer_ssnid) and account.account_type == account_type:
                account.amount = account.amount + int(withdraw_amount)
                account.message = 'Deposit successfully done.'
                account.date_created = datetime.utcnow()
                transaction_id = ''.join(random.choices(string.digits, k=8))
                transaction = Transaction(id=transaction_id,account_id=account_id,ssnid=customer_ssnid,account_type=account_type,message="Deposit",amount=withdraw_amount)
                db.session.add(transaction)
                db.session.commit()
                return render_template('message.html', account=account)
        except Exception as e:
            return render_template('deposit.html', error="There is no account with this SSNID "+str(customer_ssnid)+" and account id "+str(account_id)+". Enter correct Account ID.")
    else:
        return render_template('deposit.html')


@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if not g.user:
        return redirect('/login')
    if request.method == 'POST':
        customer_ssnid = request.form['customerssnid']
        source_account_type = request.form['sourceacctype']
        target_account_type = request.form['targetacctype']
        transfer_amount = request.form['transferamount']
        try:
            source_account = Account.query.filter(Account.ssnid==customer_ssnid,Account.account_type==source_account_type).all()[0]
        except Exception as e:
            return render_template('transfer.html', error="We didn't find "+ source_account_type +" account for customer SSNID "+ str(customer_ssnid) +".")
        try:
            target_account = Account.query.filter(Account.ssnid==customer_ssnid,Account.account_type==target_account_type).all()[0]
        except Exception as e:
            return render_template('transfer.html', error="We didn't find "+ target_account_type +" account for customer SSNID "+ str(customer_ssnid) +".")
        if source_account.amount < int(transfer_amount):
            return render_template('transfer.html', error="There is no sufficient balance in "+ source_account_type +" account for customer SSNID "+ str(customer_ssnid) +".The Total balance in "+ source_account_type +" account is "+ str(source_account.amount) +".")
        if source_account.ssnid == int(customer_ssnid) and target_account.ssnid == int(customer_ssnid):
            source_account.amount = source_account.amount - int(transfer_amount)
            target_account.amount = target_account.amount + int(transfer_amount)
            source_account.message = 'Amount deducted Successfully.'
            target_account.message = 'Amount transfered Successfully.'
            source_account.date_created = datetime.utcnow()
            target_account.date_created = datetime.utcnow()
            transaction_id = ''.join(random.choices(string.digits, k=8))
            transaction = Transaction(id=transaction_id,account_id=source_account.id,ssnid=source_account.ssnid,account_type=source_account_type,message="Withdraw",amount=transfer_amount)
            db.session.add(transaction)
            transaction_id = ''.join(random.choices(string.digits, k=8))
            transaction = Transaction(id=transaction_id,account_id=target_account.id,ssnid=target_account.ssnid,account_type=target_account_type,message="deposit",amount=transfer_amount)
            db.session.add(transaction)
            db.session.commit()
            return render_template('message.html', account=source_account)
    else:
        return render_template('transfer.html')


@app.route('/customer_status')
def customer_status():
    if not g.user:
        return redirect('/login')
    customers = Customer.query.all()
    if customers:
        return render_template('customerstatus.html', customers=customers)
    else:
        return render_template('customerstatus.html', error="No Customer found in your database")
 

@app.route('/status_of_individual_customer/<int:id>')
def status_of_individual_customer(id):
    if not g.user:
        return redirect('/login')
    customer = Customer.query.get_or_404(id)
    return render_template('searchcust.html', customer=customer)



@app.route('/account_status')
def account_status():
    if not g.user:
        return redirect('/login')
    accounts = Account.query.all()
    if accounts:
        return render_template('accountstatus.html', accounts=accounts)
    else:
        return render_template('accountstatus.html', error="No Account found in your database")
 

@app.route('/statement', methods=['GET', 'POST'])
def statement():
    if not g.user:
        return redirect('/login')
    if request.method == 'POST':
        customer_ssnid = request.form['ssnid']
        account_id = request.form['accountid']
        try:
            transactions = Transaction.query.filter(Transaction.ssnid==customer_ssnid,Transaction.account_id==account_id).all()
        except Exception as e:
            return render_template('statement.html', error="We didn't find any tansactions on this account ID "+ str(account_id) +".")
        if len(transactions) > 0:
            return render_template('accountstatement.html', transactions=transactions)
        else:
            return render_template('statement.html', error="We didn't find any tansactions on this account ID "+ str(account_id) +".")
    else:
        return render_template('statement.html')


@app.route('/pdf/<int:ssnid>/<int:id>')
def pdf(ssnid,id):
    try:
        transactions = Transaction.query.filter(Transaction.ssnid==ssnid,Transaction.account_id==id).all()
    except Exception as e:
        return render_template('statement.html', error="We didn't find any tansactions on this account ID "+ str(id) +".")
    if len(transactions) > 0:
        try:
            p = render_template('pdf.html', transactions=transactions)
            pdf = pdfkit.from_string(p, False,configuration=config)
            response = make_response(pdf)
            response.headers['Content-type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'attachment;filename=output.pdf'
            return response
        except Exception as e:
            return render_template('message.html', message="Something went wrong. Make sure that you have installed wkhtmltopdf in your computer in C drive in programfiles folder")


@app.route('/excel/<int:ssnid>/<int:id>')
def excel(ssnid,id):
    try:
        transactions = Transaction.query.filter(Transaction.ssnid==ssnid,Transaction.account_id==id).all()
    except Exception as e:
        return render_template('statement.html', error="We didn't find any tansactions on this account ID "+ str(id) +".")
    if len(transactions) > 0:
        try:
            output = io.BytesIO()
            #create WorkBook object
            workbook = xlwt.Workbook()
            #add a sheet
            sh = workbook.add_sheet('Transaction Report')
             
            #add headers
            sh.write(0, 0, 'id')
            sh.write(0, 1, 'account_id')
            sh.write(0, 2, 'customer_ssnid')
            sh.write(0, 3, 'account_type')
            sh.write(0, 4, 'message')
            sh.write(0, 5, 'date_created')
            sh.write(0, 6, 'amount')

             
            idx = 0
            for row in transactions:
                sh.write(idx+1, 0, str(row.id))
                sh.write(idx+1, 1, row.account_id)
                sh.write(idx+1, 2, row.ssnid)
                sh.write(idx+1, 3, row.account_type)
                sh.write(idx+1, 4, row.message)
                sh.write(idx+1, 5, row.date_created.strftime('%m/%d/%Y %H:%M:%S %Z'))
                sh.write(idx+1, 6, row.amount)
                idx += 1
             
            workbook.save(output)
            output.seek(0)
             
            return Response(output, mimetype="application/ms-excel", headers={"Content-Disposition":"attachment;filename=transaction.xls"})
        except Exception as e:
            pass




if __name__ == "__main__":
    app.run(debug=True)