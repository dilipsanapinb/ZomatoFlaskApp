from flask import Flask, request, render_template, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO, emit
from datetime import datetime
import uuid
from google.cloud import dialogflow

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///menu.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
socketio = SocketIO(app)

# Database Models
class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    availability = db.Column(db.Boolean, nullable=False)
    average_rating=db.Column(db.Float, default=0.0)


    def calculate_average_rating(self):
        ratings=Rating.query.filter_by(dish_id=self.id).all()
        if ratings:
            total_ratings=sum(rating.value for rating in ratings)
            self.average_rating=total_ratings/len(ratings)
        else:
            self.average_rating=0.0

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float, nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'), nullable=False)
    dish = db.relationship('Dish', backref=db.backref('ratings', cascade='all, delete-orphan'))


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    dish_ids = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)

@app.route('/')
def home():
    return render_template('/index.html')

@app.route('/menu')
def read_menu():
    menu = Dish.query.all()
    return render_template('menu.html', menu=menu)

@app.route('/menu/add', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        id=len(Dish.query.all())+1
        name = request.form['name']
        price = float(request.form['price'])
        availability = bool(request.form['availability'])
        dish = Dish(id=id,name=name, price=price, availability=availability)
        db.session.add(dish)
        db.session.commit()

        dish.calculate_average_rating()
        db.session.commit()

        return redirect('/menu')
    return render_template('add_dish.html')

@app.route('/dish/rate',methods=['POST'])
def rate_dish():
    dish_id = request.form.get('dish_id')
    if not dish_id:
        return 'Invalid dish ID'

    try:
        dish_id = int(dish_id)
        dish= Dish.query.get(dish_id)
    except ValueError:
        return 'Invalid dish ID'
    
    rating_value = float(request.form.get('rating'))
    rating=Rating(value=rating_value,dish=dish)
    db.session.add(rating)
    db.session.commit()

    dish.calculate_average_rating()
    db.session.commit()

    return redirect('/menu')

@app.route('/menu/update/<int:dish_id>', methods=['GET', 'POST'])
def update(dish_id):
    dish = Dish.query.get(dish_id)

    if dish is None:
        return "Dish not found"
    
    if request.method == 'POST':
        dish.name = request.form.get('name')
        dish.price = float(request.form.get('price'))
        dish.availability = request.form.get('availability') == 'True'
        db.session.commit()
        return redirect('/menu')
    
    return render_template('update_dish.html', dish=dish)

@app.route('/menu/delete/<int:dish_id>', methods=['GET', 'POST'])
def deleteDish(dish_id):
    dish = Dish.query.get(dish_id)

    if dish is None:
        return "Dish not found"

    if request.method == 'POST':
        db.session.delete(dish)
        db.session.commit()
        return redirect('/menu')

    return render_template('delete.html', dish=dish)

@app.route('/menu/update_availability/<int:dish_id>', methods=['GET', 'POST'])
def update_avail(dish_id):
    dish = Dish.query.get(dish_id)
    if dish is None:
        return "Dish not found"
    
    if request.method == "POST":
        dish.availability = request.form.get('availability') == 'True'
        db.session.commit()
        return redirect('/menu')
    
    return render_template('update_availability.html', dish=dish)

@app.route('/orders')
def orders_display():
    orders = Order.query.all()
    return render_template('orders.html', orders=orders)

@app.route('/orders/new', methods=['GET', 'POST'])
def new_order_add():
    if request.method == 'POST':
        customer_name=request.form.get('customer_name')
        dish_ids = [int(dish_id.strip()) for dish_id in request.form.get('dish_ids').split(',') if dish_id.strip()]

        dish_ids_str=','.join(map(str,dish_ids))
        order_id=len(Order.query.all())+1
        new_order=Order(id=order_id,customer_name=customer_name,dish_ids=dish_ids_str,status='placed',timestamp=datetime.now())
        db.session.add(new_order)
        db.session.commit()
        return redirect('/orders')
    
    return render_template('new_order.html')

@app.route('/orders/review')
def review_orders_data():
    orders = Order.query.all()
    return render_template('review_orders.html', orders=orders)

@app.route('/orders/update/<int:order_id>', methods=['GET', 'POST'])
def update_order(order_id):
    order = Order.query.get(order_id)

    if order is None:
        return "Order not found"

    if request.method == 'POST':
        new_status = request.form.get('status')
        order.status = new_status
        db.session.commit()

        socketio.emit('order_status_updated', {'orderId': order_id, 'newStatus': new_status})

        return redirect('/orders')

    return render_template('update_order.html', order=order)

@app.route('/socket.io/socket.io.js')
def serve_socketio():
    return app.send_static_file('socket.io.js')

@app.route('/exit', methods=['GET', 'POST'])
def exit_operation():
    if request.method == 'POST':
        return "<h3>Thank you for using Khana Khajana! Have a great day!</h3>"
    
    return render_template('exit.html')

@app.route('/chatbot', methods=['POST'])
def chatbotGet():
    user_query = request.form['query']

    dialogflow_response = get_dialogflow_response(user_query)
    chatbot_response = dialogflow_response.query_result.fulfillment_text
    return jsonify({'response': chatbot_response})

def get_dialogflow_response(user_query):
    session_client = dialogflow.SessionsClient()
    session_id = str(uuid.uuid4())
    session = session_client.session_path('project-id', session_id)
    text_input = dialogflow.types.TextInput(text=user_query, language_code='en')
    query_input = dialogflow.types.QueryInput(text=text_input)
    response = session_client.detect_intent(session=session, query_input=query_input)
    return response

@socketio.on('connect')
def handle_connect():
    emit('status_update', {'message': 'Connected to the server.'})

if __name__ == '__main__':
    # db.create_all()
    app.run(debug=True)
    socketio.run(app, debug=True)
