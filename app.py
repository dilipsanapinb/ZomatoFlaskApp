from flask import Flask,request,render_template,redirect
app=Flask(__name__)

menu=[
        {'id':1,'name':"Samosa",'price':50, 'availability': True},
        {'id':2,'name':'Pizza','price':300,'availability': True},
        {'id':3,'name':'Burger','price':100,'availability': False}
    ]

@app.route('/')
def home():
    return "<h3>Welcome to Khana Khajana! We deliver  cilinary delights to your doorstep.</h3>"

@app.route('/menu')
def read():
    return render_template('/menu.html', entries=menu)


@app.route('/menu/add',methods=['GET','POST'])
def create():
    if request.method=='POST':
        name=request.form.get('name')
        price=float(request.form.get('price'))
        availability=request.form.get('availability')

        new_dish={
            'id':len(menu)+1,
            'name':name,
            'price':price,
            'availability':availability
        }
        menu.append(new_dish)
        return redirect('/menu')
    
    return render_template('add_dish.html')


@app.route('/menu/update/<int:dish_id>',methods=['GET','POST'])
def update(dish_id):
    dish=next((item for item in menu if item['id']==dish_id),None)

    if dish is None:
        return "Dish not found"
    
    if request.method=='POST':
        dish['name'] = request.form.get('name')
        dish['price'] = float(request.form.get('price'))
        dish['availability'] = request.form.get('availability')
        return redirect('/menu')
    
    return render_template('/update_dish.html',dish=dish)



@app.route('/menu/delete/<int:dish_id>', methods=['GET', 'POST'])
def deleteDish(dish_id):
    dish = next((item for item in menu if item['id'] == dish_id), None)

    if dish is None:
        return "Dish not found"

    if request.method == 'POST':
        menu.remove(dish)
        return redirect('/menu')

    return render_template('delete.html', dish=dish)

@app.route('/menu/update_availability/<int:dish_id>', methods=['GET','POST'])
def update_avail(dish_id):
    dish=next((item for item in menu if item['id']==dish_id),None)

    if dish is None:
        return "Dish not found"
    
    if request.method=="POST":
        dish['availability']=request.form.get('availability')=='True'
        return redirect('/menu')
    
    return render_template('update_availability.html', dish=dish)

from datetime import datetime

orders = []

@app.route('/orders')
def orders_display():
    return render_template('orders.html', orders=orders)

@app.route('/orders/new', methods=['GET', 'POST'])
def new_order_add():
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        dish_ids = [int(dish_id.strip()) for dish_id in request.form.get('dish_ids').split(',') if dish_id.strip()]
        order_id = len(orders) + 1
        order = {
            'id': order_id,
            'customer_name': customer_name,
            'dish_ids': dish_ids,
            'status': 'received',
            'timestamp': datetime.now()
        }
        orders.append(order)
        return redirect('/orders')
    
    return render_template('new_order.html')

# update order status

@app.route('/orders/update/<int:order_id>', methods=['GET', 'POST'])
def update_order(order_id):
    order = next((item for item in orders if item['id'] == order_id), None)

    if order is None:
        return "Order not found"

    if request.method == 'POST':
        order['status'] = request.form.get('status')
        return redirect('/orders')

    return render_template('update_order.html', order=order)

@app.route('/orders/review')
def review_orders_data():
    return render_template('review_orders.html', orders=orders)

@app.route('/exit', methods=['GET', 'POST'])
def exit_operation():
    if request.method == 'POST':
        # Perform any necessary operations before exiting
        # e.g., save data, close connections, etc.
        return "<h3>Thank you for using Khana Khajana! Have a great day!</h3>"
    
    return render_template('exit.html')


if __name__=='__main__':
    app.run(debug=True)