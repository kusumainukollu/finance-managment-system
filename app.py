from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime
from flask import flash
from models import db, Transactions, User, UserBudget
from werkzeug.security import generate_password_hash, check_password_hash
import os
import pandas as pd

app = Flask(__name__)
from flask import Flask

# app = Flask(
#     __name__,
#     template_folder="../templates",  # Adjust path to the templates folder
#     static_folder="../static"       # Adjust path to the static folder
# )

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'finance_tracker.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = '3cdb21726265fc1194f5e0cc73a529112cc0477f2bc015e3'

db.init_app(app)
# initialize_routes(app)
# @app.before_first_request
def create_tables():    
    db.create_all()

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/index', methods=['GET'])
def index():
    if 'user_id' in session:  
        user_id = session['user_id']
        transactions = Transactions.query.filter_by(user_id=user_id).all() 
        return render_template('index.html', transactions=transactions) 
    else:
        return render_template('landing.html') 


    
from flask import render_template, request, redirect, url_for, session

@app.route('/set_category_budget', methods=['POST'])
def set_category_budget():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Ensure the user is logged in

    user_id = session['user_id']  # Get the logged-in user's ID

    if request.method == 'POST':
        try:
            # Retrieve budget values from the form
            monthly_salary = float(request.form.get('monthly_salary', 0))
            food_budget = float(request.form.get('food_budget', 0))
            transport_budget = float(request.form.get('transport_budget', 0))
            entertainment_budget = float(request.form.get('entertainment_budget', 0))
            bills_budget = float(request.form.get('bills_budget', 0))
            other_budget = float(request.form.get('other_budget', 0))

            # Validate input values
            if monthly_salary < 0 or food_budget < 0 or transport_budget < 0 or entertainment_budget < 0 or bills_budget < 0 or other_budget < 0:
                flash("Budget values cannot be negative.", "danger")
                return redirect(url_for('index'))

            # Check if the user already has a budget in the database
            existing_budget = UserBudget.query.filter_by(user_id=user_id).first()

            if existing_budget:
                # Update the existing budget
                existing_budget.food = food_budget
                existing_budget.transport = transport_budget
                existing_budget.entertainment = entertainment_budget
                existing_budget.bills = bills_budget
                existing_budget.other = other_budget
            else:
                # Create a new budget entry
                new_budget = UserBudget(
                    user_id=user_id,
                    food=food_budget,
                    transport=transport_budget,
                    entertainment=entertainment_budget,
                    bills=bills_budget,
                    other=other_budget
                )
                db.session.add(new_budget)

            # Commit changes to the database
            db.session.commit()

            # Update session values
            session['monthly_salary'] = monthly_salary
            session['user_budgets'] = {
                'food': food_budget,
                'transport': transport_budget,
                'entertainment': entertainment_budget,
                'bills': bills_budget,
                'other': other_budget
            }

            flash("Budget has been set successfully!", "success")
            return redirect(url_for('index'))

        except ValueError:
            flash("Invalid input. Please ensure all fields contain valid numbers.", "danger")
            return redirect(url_for('index'))





def get_db_connection():
    conn = sqlite3.connect('budget_tracker.db') 
    conn.row_factory = sqlite3.Row
    return conn

def get_all_transactions():
    conn = get_db_connection()
    transactions = conn.execute('SELECT * FROM transactions').fetchall() 
    conn.close()
    return transactions




@app.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_budgets_record = UserBudget.query.filter_by(user_id=user_id).first()
    user_budgets = {}
    if user_budgets_record:
        # Convert the UserBudget object to a dictionary
        user_budgets = {
            'food': user_budgets_record.food,
            'transport': user_budgets_record.transport,
            'entertainment': user_budgets_record.entertainment,
            'bills': user_budgets_record.bills,
            'other': user_budgets_record.other,
        }

    if request.method == 'POST':
        try:
            # Retrieve form data
            date = request.form['date']
            type_ = request.form['type']
            category = request.form['category']
            amount = float(request.form['amount'])
            description = request.form.get('description', '')

            # Check if a budget exists for the selected category
            category_budget = user_budgets.get(category)
            if category_budget is None:
                flash(f"No budget is defined for the category '{category}'. Please set it before adding transactions.", "danger")
                return render_template('add.html', user_budgets=user_budgets)

            # Calculate total category expenses
            total_category_expenses = db.session.query(db.func.sum(Transactions.amount)).filter(
                Transactions.user_id == user_id,
                Transactions.type == 'Expense',
                Transactions.category == category
            ).scalar() or 0

            # Check if the transaction exceeds the category budget
            if type_ == 'Expense' and (total_category_expenses + amount) > category_budget:
                flash(f"Error: Adding this transaction exceeds the budget for '{category}'! Budget: ₹{category_budget}, Spent: ₹{total_category_expenses}.", "danger")
                return render_template('add.html', user_budgets=user_budgets)

            # Add the transaction to the database
            transaction = Transactions(
                user_id=user_id,
                date=date,
                type=type_,
                category=category,
                amount=amount,
                description=description
            )
            db.session.add(transaction)
            db.session.commit()

            flash("Transaction added successfully!", "success")
            return redirect(url_for('index'))

        except Exception as e:
            flash(f"Error adding transaction: {e}", "danger")
            return render_template('add.html', user_budgets=user_budgets)

    return render_template('add.html', user_budgets=user_budgets)



import pandas as pd
from flask import send_file, session, flash, redirect, url_for
from io import BytesIO

@app.route('/download_transactions')
def download_transactions():
    # Ensure the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    username = session.get('username', 'user')  # Get username from session, default to 'user'

    # Fetch the user's transactions from the database
    transactions = Transactions.query.filter_by(user_id=user_id).all()

    # Convert the transactions data to a list of dictionaries
    transaction_data = []
    for transaction in transactions:
        transaction_data.append({
            'Date': transaction.date,
            'Type': transaction.type,
            'Category': transaction.category,
            'Amount': transaction.amount,
            'Description': transaction.description
        })

    # Create a Pandas DataFrame
    df = pd.DataFrame(transaction_data)

    # Create a BytesIO object to store the Excel file
    output = BytesIO()

    # Write the DataFrame to the BytesIO object as an Excel file
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Transactions')

    # Save the Excel file
    output.seek(0)

    # Set the filename to the username followed by _transactions.xlsx
    filename = f"{username}_transactions.xlsx"

    # Send the file as a response for download
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/profile', methods=['GET'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id']) 
    
    if not user:
        return redirect(url_for('login'))

    return render_template('profile.html', user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login')) 

    user = User.query.get(session['user_id']) 

    if request.method == 'POST':
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.email = request.form['email']
        user.phone = request.form['phone']
        user.company = request.form['company']
        user.dob = request.form['dob']
        
        try:
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for('profile')) 
        except Exception as e:
            flash(f"Error updating profile: {e}", "error")
            return redirect(url_for('edit_profile')) 

    return render_template('edit_profile.html', user=user) 


from flask import render_template
from models import db, Transactions

@app.route('/summary')
def summary():
    # Ensure that the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    # Fetch the logged-in user's ID from the session
    user_id = session['user_id']

    # Fetch the sum of income and expenses by category for the logged-in user
    category_expenses = db.session.query(Transactions.category, db.func.sum(Transactions.amount).label('total_amount'))\
        .filter(Transactions.type == 'Expense', Transactions.user_id == user_id)  \
        .group_by(Transactions.category).all()

    # Fetch the total income for the logged-in user
    total_income_transactions = db.session.query(db.func.sum(Transactions.amount).label('total_income'))\
        .filter(Transactions.type == 'Income', Transactions.user_id == user_id).scalar() or 0  

    # Get the user's monthly salary from session
    monthly_salary = session.get('monthly_salary', 0) 

    # Calculate total income (monthly salary + income from transactions)
    total_income = monthly_salary + total_income_transactions

    # Prepare the data for chart (pie and bar chart)
    categories = [expense.category for expense in category_expenses]
    amounts = [expense.total_amount for expense in category_expenses]

    chart_data = {
        'pie': {
            'labels': categories,
            'datasets': [{
                'label': 'Expenses',
                'data': amounts,
                'backgroundColor': ['#27ae60', '#3498db', '#f39c12', '#e74c3c', '#9b59b6'],
                'borderColor': '#2c3e50',
                'borderWidth': 1
            }]
        },
        'bar': {
            'labels': categories,
            'datasets': [{
                'label': 'Expenses',
                'data': amounts,
                'backgroundColor': '#1abc9c',
                'borderColor': '#16a085',
                'borderWidth': 1
            }]
        }
    }

    total_expenses = sum(amounts)
    remaining_budget = total_income - total_expenses

    # Render the template with the data
    return render_template('summary.html', 
                           category_expenses=category_expenses,
                           chart_data=chart_data,
                           total_income=total_income,
                           total_expenses=total_expenses,
                           remaining_budget=remaining_budget)


@app.route('/delete/<int:transaction_id>', methods=['POST'])
def delete_transaction(transaction_id):
    try:
        transaction = Transactions.query.get(transaction_id)
        if transaction:
            db.session.delete(transaction)
            db.session.commit()
            flash("Transaction deleted successfully.")
        else:
            flash("Transaction not found.")
    except Exception as e:
        print(f"Error deleting transaction: {e}")
        flash("An error occurred while deleting the transaction.")
    return redirect(url_for('index'))

@app.route('/edit/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Ensure the user is logged in

    user_id = session['user_id']  # Get the logged-in user's ID
    transaction = Transactions.query.get(transaction_id)

    if not transaction or transaction.user_id != user_id:
        flash("Transaction not found.")
        return redirect(url_for('index'))

    # Retrieve user's budgets from the database
    user_budget = UserBudget.query.filter_by(user_id=user_id).first()

    if not user_budget:
        flash("No budget defined for this user. Please set a budget first.", "danger")
        return redirect(url_for('index'))

    # Convert the budget to a dictionary for easy access
    category_budgets = {
        'food': user_budget.food,
        'transport': user_budget.transport,
        'entertainment': user_budget.entertainment,
        'bills': user_budget.bills,
        'other': user_budget.other,
    }

    if request.method == 'POST':
        try:
            # Get the updated values
            updated_date = request.form['date']
            updated_type = request.form['type']
            updated_category = request.form['category']
            updated_amount = float(request.form['amount'])
            updated_description = request.form['description']

            # Validate the budget
            category_budget = category_budgets.get(updated_category.lower(), None)
            if category_budget is None:
                flash(f"No budget is defined for the category '{updated_category}'.", "danger")
                return render_template('edit_transaction.html', transaction=transaction)

            # Calculate total expenses for the category (excluding the current transaction)
            total_category_expenses = db.session.query(db.func.sum(Transactions.amount)).filter(
                Transactions.user_id == user_id,
                Transactions.type == 'Expense',
                Transactions.category == updated_category,
                Transactions.id != transaction_id  # Exclude the current transaction
            ).scalar() or 0

            # Check if the updated transaction exceeds the category budget
            if updated_type == 'Expense' and (total_category_expenses + updated_amount) > category_budget:
                flash(
                    f"Error: Updating this transaction will exceed the budget for '{updated_category}'. "
                    f"Budget: {category_budget}, Spent: {total_category_expenses}.",
                    "danger"
                )
                return render_template('edit_transaction.html', transaction=transaction)

            # Calculate total expenses across all categories (excluding the current transaction)
            total_expenses = db.session.query(db.func.sum(Transactions.amount)).filter(
                Transactions.user_id == user_id,
                Transactions.type == 'Expense',
                Transactions.id != transaction_id  # Exclude the current transaction
            ).scalar() or 0

            # Check if the updated transaction exceeds the overall budget
            monthly_salary = session.get('monthly_salary', 0)
            if updated_type == 'Expense' and (total_expenses + updated_amount) > monthly_salary:
                flash(
                    f"Error: Updating this transaction will exceed your overall budget. "
                    f"Monthly Salary: {monthly_salary}, Spent: {total_expenses}.",
                    "danger"
                )
                return render_template('edit_transaction.html', transaction=transaction)

            # Update the transaction
            transaction.date = updated_date
            transaction.type = updated_type
            transaction.category = updated_category
            transaction.amount = updated_amount
            transaction.description = updated_description
            db.session.commit()

            flash("Transaction updated successfully.", "success")
            return redirect(url_for('index'))

        except Exception as e:
            print(f"Error updating transaction: {e}")
            flash("An error occurred while updating the transaction.", "danger")

    return render_template('edit_transaction.html', transaction=transaction)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id 
            return redirect(url_for('index')) 
        
        return 'Invalid credentials. Please try again.'
    
    return render_template('login.html')



from flask import render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash
from models import db, User  

@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        # Get form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        company = request.form['company']
        dob = request.form['dob']  
        password = request.form['password']


        hashed_password = generate_password_hash(password)

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            phone=phone,
            company=company,
            dob=dob, 
            password=hashed_password
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Account created successfully. Please log in.")
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Error while inserting user: {e}")
            flash("An error occurred while creating your account.")
            return render_template('sign_up.html')

    return render_template('sign_up.html')




@app.route('/logout')
def logout():
    session.pop('user_id', None) 
    return redirect(url_for('login'))

if __name__ == '__main__':
    import init_db
    
    app.run(debug=True)
