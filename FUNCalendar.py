#coding: UTF-8

from flask import Flask,request,render_template,jsonify,Response,abort,make_response
from flask_restful import Resource,Api
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
import sys
import mysql.connector
import hashlib
import json

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://URL?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
auth = HTTPBasicAuth()
db = SQLAlchemy(app)

# json format #
''' jsonレスポンスを作成 '''
def json_format(code, message, keys = None, main_contents = None, last_added_id = 0):
    status = {'code':code ,'message':message}
    if(main_contents is None or keys is None or len(keys) != len(main_contents)):
        if(last_added_id != 0):
            status["last_added_id"] = last_added_id
        return make_response(jsonify(status=status) ,code)
    else:
        response = dict(zip(keys,main_contents))
    return make_response(jsonify(status=status,result=response), code)


# error #
''' エラーハンドラー '''
@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(404)
@app.errorhandler(406)
def error_handler(error):
    message = ''
    if(error.code == 400):
        message = 'Bad Request'
    elif(error.code == 401):
        message = 'Unauthorized'
    elif(error.code == 404):
        message = 'Not Found'
    elif(error.code == 406):
        message = 'Not Acceptable'
    return json_format(error.code,message)

''' 認証エラー '''
@auth.error_handler
def auth_error_handler():
    message = 'Unauthorized'
    return json_format(401, message)



# Hash #
''' パスワードをハッシュ化(生成・検索) '''
def hash_password(password,salt):
    pwd = password
    s = salt
    for i in range(10):
        s = hashlib.sha256(s.encode('utf-8')).hexdigest()
        pwd = hashlib.sha256(pwd.encode('utf-8')+s.encode('utf-8')).hexdigest()
    return pwd


### DataBase Object ###
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String(64), unique = True)
    email = db.Column(db.String(64), unique = True)
    pwdhash = db.Column(db.String(256))
    wish_items = db.relationship("WishItem", backref = "user", lazy='immediate')
    todo_items = db.relationship("ToDoItem", backref ="user", lazy='immediate')
    household_accounts_items = db.relationship("HouseholdAccountsItem", backref ="user", lazy='immediate')
    #balance_items = db.relationship("BalanceItem", backref ="user", lazy='immediate')

    def __init__(self,name,email,password):
        self.name = name
        self.email = email
        self.set_password(password)
   
    def set_password(self, password):
        self.pwdhash = hash_password(password,self.email)

    def serialize(self):
        return {
            'id'      : self.id,
            'name'    : self.name,
            'email'   : self.email
        }


class WishItem(db.Model):
    __tablename__ = 'wish_item'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String(32))
    price = db.Column(db.String(16))
    date = db.Column(db.String(16))
    is_bought = db.Column(db.String(8))
    todo_id = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __init__(self, name, price, date, is_bought, todo_id, user_id):
        self.name = name
        self.price = price
        self.date = date
        self.is_bought = is_bought
        self.todo_id = todo_id
        self.user_id = user_id

    def serialize(self):
        return {
            'id'        : self.id,
            'name'      : self.name,
            'price'     : self.price,
            'date'      : self.date,
            'is_bought' : self.is_bought,
            'todo_id'   : self.todo_id
        }


class ToDoItem(db.Model):
    __tablename__ = 'todo_item'
    id = db.Column(db.Integer,primary_key = True, autoincrement = True)
    description = db.Column(db.String(64))
    date = db.Column(db.String(16))
    priority = db.Column(db.String(8))
    is_completed = db.Column(db.String(8))
    wish_id = db.Column(db.Integer)

    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))

    def __init__(self, description, date, priority,is_completed, wish_id, user_id):
        self.description = description
        self.date = date
        self.priority = priority
        self.is_completed = is_completed
        self.wish_id = wish_id
        self.user_id = user_id

    def serialize(self):
        return {
            'id'           : self.id,
            'description'  : self.description,
            'date'         : self.date,
            'priority'     : self.priority,
            'is_completed' : self.is_completed,
            'wish_id'      : self.wish_id
        }


class HouseholdAccountsItem(db.Model):
    __tablename__ = 'household_accounts_item'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String(64))
    price = db.Column(db.String(16))
    date = db.Column(db.String(16))
    summary_category = db.Column(db.String(32))
    detail_category = db.Column(db.String(32))
    storage_type = db.Column(db.String(16))
    is_out_goings = db.Column(db.String(32))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __init__(self, name, price, date, summary_category, detail_category, storage_type, is_out_goings, user_id):
        self.name = name
        self.price = price
        self.date = date
        self.summary_category = summary_category
        self.detail_category = detail_category
        self.storage_type = storage_type
        self.is_out_goings = is_out_goings
        self.user_id = user_id

    def serialize(self):
        return {
            'id'               : self.id, 
            'name'             : self.name,
            'price'            : self.price,
            'date'             : self.date,
            'summary_category' : self.summary_category,
            'detail_category'  : self.detail_category,
            'storage_type'     : self.storage_type,
            'is_out_goings'    : self.is_out_goings
        }

'''
class BalanceItem(db.Model):
    __tablename__ = 'balance_item'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    balance_type = db.Column(db.String(16))
    price = db.Column(db.String(16))
    image = db.Column(db.String(64))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, balance_type, price, image, user_id):
        self.balance_type = balance_type
        self.price = price
        self.image = image
        self.user_id = user_id

    def serialize(self):
        return {
            'balance_type' : self.balance_type,
            'price'        : self.price,
            'image'        : self.image
        }
'''

# BasicAuth #
@staticmethod
@auth.verify_password
def verify(username,password):
    user = db.session.query(User).filter_by(name=username).first()
    if(user == None):
        return False
    pwd = hash_password(password,user.email)
    return user.pwdhash == pwd


### Pages ###
@app.route("/")
def hello():
    return "<span style='color:red'>Hello,FUNCalendar!</span>"

@app.route("/errorpage")
def notFound():
    return render_template('404.html')
 
@app.route("/create")
def createdb():
    db.create_all()
    return "success!!"


### APIs ###
class UserAPI(Resource):
    @auth.login_required
    def get(self, user_name = None):
        name = user_name
        if(user_name is None):
            name = auth.username()
        user = db.session.query(User).filter_by(name = name).first()
        return json_format(200,'Getting UserInfo is success',['user'],[user.serialize()])
    # あとで変える #    
#    @auth.login_required
    def post(self):
        user_json = request.json['user']
        user_name = user_json['user_name']
        email = user_json['email']
        password = user_json['password']
        if(user_name == None or email == None or password == None):
            abort(400)
        user = User(name = user_name,email = email, password = password)
        db.session.add(user)
        db.session.commit()
        return json_format(201,"UserInfo is created")


class WishListAPI(Resource):
    @auth.login_required
    def get(self, id = None):
        user = db.session.query(User).filter_by(name = auth.username()).first()
        if(user is None):
            return json_format(401,'unauthorized')
        if(id is None):
            wish_items = user.wish_items
        else:
            wish_items = user.wish_items
            temp = list()
            for wish_item in wish_items:
                if(wish_item.id == id):
                    temp.append(wish_item)
                    break
            wish_items = temp
        if(not wish_items):
            return json_format(404,'WishItem is not found')
        wish_items_json = []
        for wish_item in wish_items:
            wish_items_json.append(wish_item.serialize())
        return json_format(200,'WishItem is found',['wish_item'],[wish_items_json])

    @auth.login_required
    def post(self):
        wish_items_json = request.json['wish_item']
        if(wish_items_json is None):
            return json_format(400,'Invalid Request Error')
        user_id = db.session.query(User).filter_by(name = auth.username()).first().id
        if(isinstance(wish_items_json, dict)):
            temp = wish_items_json
            wish_items_json = list()
            wish_items_json.append(temp)
        for wish_item_json in wish_items_json:
            name = wish_item_json['name']
            price = wish_item_json['price']
            date = wish_item_json['date']
            is_bought = wish_item_json['is_bought']
            todo_id = wish_item_json['todo_id']
            if(name is None or price is None or date is None or is_bought is todo_id is None):
                return json_format(400,'Invalid Request Error') 
            wish_item = WishItem(name, price, date, is_bought, todo_id, user_id)
            db.session.add(wish_item)
        db.session.commit()
        return json_format(201, 'WishItem is Created', last_added_id = wish_item.id)

    @auth.login_required
    def put(self, id):
        user = db.session.query(User).filter_by(name = auth.username()).first()
        if(user is None):
            return json_format(401,'unauthorized')
        wish_item = None
        for temp in user.wish_items:
            if(temp.id == id):
                wish_item = temp
                break
        if(wish_item is None):
            return json_format(404,'WishItem is not found')
        wish_item_json = request.json['wish_item']
        wish_item.name = wish_item_json['name']
        wish_item.price = wish_item_json['price']
        wish_item.date = wish_item_json['date']
        wish_item.is_bought = wish_item_json['is_bought']
        wish_item.todo_id = wish_item_json['todo_id']
        db.session.commit()
        return json_format(200,'WishItem is Updated')
    
    @auth.login_required
    def delete(self, id):
        user = db.session.query(User).filter_by(name = auth.username()).first()
        if(user is None):
            return json_format(401,'unauthorized')
        wish_item = None
        for temp in user.wish_items:
            if(temp.id == id):
                wish_item = temp
                break
        if(wish_item is None):
             return json_format(404,'WishItem is not found')
        db.session.delete(wish_item)
        db.session.commit()
        return json_format(200,'WishItem is Deleted')


class ToDoAPI(Resource):
    @auth.login_required
    def get(self, id = None):
        user = db.session.query(User).filter_by(name = auth.username()).first()
        if(user is None):
            return json_format(401,'unauthorized')
        if(id is None):
            todo_items = user.todo_items
        else:
            todo_items = user.todo_items
            temp = list()
            for todo_item in todo_items:
                if(todo_item.id == id):
                    temp.append(todo_item)
                    break
            todo_items = temp
        if(not todo_items):
            return json_format(404,'ToDo is not found')
        todo_items_json =[]
        for todo_item in todo_items:
            todo_items_json.append(todo_item.serialize())
        return json_format(200, 'ToDo is found',['todo_item'],[todo_items_json])

    @auth.login_required
    def post(self):
        todo_items_json = request.json['todo_item']
        if(todo_items_json is None):
            return json_format(400 ,'Invalid Request Error')
        user_id = db.session.query(User).filter_by(name = auth.username()).first().id
        if(isinstance(todo_items_json, dict)):
            temp = todo_items_json
            todo_items_json = list()
            todo_items_json.append(temp)
        for todo_item_json in todo_items_json:
            description = todo_item_json['description']
            date = todo_item_json['date']
            priority = todo_item_json['priority']
            is_completed = todo_item_json['is_completed']
            wish_id = todo_item_json['wish_id']
            if(description is None or date is None or priority is None or is_completed is wish_id is None):
                return json_format(400,'Invalid Request Error') 
            todo_item = ToDoItem(description, date, priority, is_completed, wish_id, user_id)
            db.session.add(todo_item)
        db.session.commit()
        return json_format(201, 'ToDoItem is Created', last_added_id = todo_item.id)

    @auth.login_required
    def put(self, id):
        user = db.session.query(User).filter_by(name =auth.username()).first()
        if(user is None):
            return json_format(401, 'unauthorized')
        todo_item = None
        for temp in user.todo_items:
            if(temp.id == id):
                wish_item = temp
                break
        if(todo_item is None):
            return json_format(404, 'ToDo is not found')
        todo_item_json = request.json['todo_item']
        todo_item.description = todo_item_json['description']
        todo_item.date = todo_item_json['date']
        todo_item.priority = todo_item_json['priority']
        todo_item.is_completed = todo_item_json['is_completed']
        todo_item.wish_id = todo_item_json['wish_id']
        db.session.commit()
        return json_format(200, 'ToDo is Updated')

    @auth.login_required
    def delete(self, id):
        user = db.session.query(User).filter_by(name =auth.username()).first()
        if(user is None):
            return json_format(401, 'unauthorized')
        todo_item = None
        for temp in user.todo_items:
            if(temp.id == id):
                todo_item = temp
                break
        if(todo_item is None):
            return json_format(404, 'ToDo is not found')
        db.session.delete(todo_item)
        db.session.commit()
        return json_format(200,'ToDo is deleted')


class HouseholdAccountsAPI(Resource):
    @auth.login_required
    def get(self, id = None):
        user = db.session.query(User).filter_by(name = auth.username()).first()
        if(user is None):
            return json_format(401, 'unauthorized')
        if(id is None):
            household_accounts_items = user.household_accounts_items
        else:
            household_accounts_items = user.household_accounts_items
            temp = list()
            for household_accounts_item in household_accounts_items:
                if(household_accounts_item.id == id):
                    temp.append(household_accounts_item)
                    break
            household_accounts_items = temp
        if(not household_accounts_items):
            return json_format(404, 'householdaccounts is not found')
        household_accounts_items_json = []
        for household_accounts_item in household_accounts_items:
            household_accounts_items_json.append(household_accounts_item.serialize())
        return json_format(200,'householdaccounts is found', ['household_accounts_item'],[household_accounts_items_json])

    @auth.login_required
    def post(self):
        household_accounts_items_json = request.json['household_accounts_item']
        if(household_accounts_items_json is None):
            return json_format(400,'Invalid Request Error')
        user_id = db.session.query(User).filter_by(name = auth.username()).first().id
        if(isinstance(household_accounts_items_json, dict)):
            temp = household_accounts_items_json
            household_accounts_items_json = list()
            household_accounts_items_json.append(temp)
        for household_accounts_item_json in household_accounts_items_json:
            name = household_accounts_item_json['name']
            price = household_accounts_item_json['price']
            date = household_accounts_item_json['date']
            summary_category = household_accounts_item_json['summary_category']
            detail_category = household_accounts_item_json['detail_category']
            storage_type = household_accounts_item_json['storage_type']
            is_out_goings = household_accounts_item_json['is_out_goings']
            if(name is None or price is None or date is None or summary_category is None or detail_category is None or storage_type is None or is_out_goings is None):
                return json_format(400, 'Invalid Request Error')
            household_accounts_item = HouseholdAccountsItem(name, price, date, summary_category, detail_category, storage_type, is_out_goings, user_id)
            db.session.add(household_accounts_item)
        db.session.commit()
        return json_format(201, 'householdaccounts is created', last_added_id = household_accounts_item.id)

    @auth.login_required
    def put(self, id):
        user = db.session.query(User).filter_by(name = auth.username()).first()
        if(user is None):
            return json_format(401, 'unauthorized')
        household_accounts_item = None
        for temp in user.household_accounts_items:
            if(temp.id == id):
                household_accounts_item = temp
                break
        if(household_accounts_item is None):
            return json_format(404,'householdaccounts is not found')
        household_accounts_item_json = request.json['household_accounts_item']
        name = household_accounts_item_json['name']
        price = household_accounts_item_json['price']
        date = household_accounts_item_json['date']
        summary_category = household_accounts_item_json['summary_category']
        detail_category = household_accounts_item_json['detail_category']
        storage_type = household_accounts_item_json['storage_type']
        is_out_goings = household_accounts_item_json['is_out_goings']
        if(name is None  or price is None or date is None or summary_category is None or detail_category is None or storage_type is None or is_out_goings is None):
                return json_format(400, 'Invalid Request Error')
        household_accounts_item.name = name
        household_accounts_item.price = price
        household_accounts_item.date = date
        household_accounts_item.summary_category = summary_category
        household_accounts_item.detail_category = detail_category
        household_accounts_item.storage_type = storage_type
        household_accounts_item.is_out_goings = is_out_goings
        db.session.commit()
        return json_format(200, 'householdaccounts is updated')

    @auth.login_required
    def delete(self, id):
        user = db.session.query(User).filter_by(name =auth.username()).first()
        if(user is None):
            return json_format(401, 'unauthorized')
        household_accounts_item = None
        for temp in user.household_accounts_items:
            if(temp.id == id):
                household_accounts_item = temp	
                break
        if(household_accounts_item is None):
            return json_format(404, 'householdacconts is not found')
        db.session.delete(household_accounts_item)
        db.session.commit()
        return json_format(200, 'householdaccounts is deleted')

'''
class BalanceListAPI(Resource):
    @auth.login_required
    def get(self, id = None):
        user = db.session.query(User).filter_by(name = auth.username()).first()
        if(user is None):
            return json_format(401, 'unauthorized')
        if(id is None):
            balance_items = user.balance_items
        else:
            balance_items = user.balance_items
            temp = list()
            for balance_item in balance_items:
                if(balance_item.id == id):
                    temp.append(balance_item)
                    break
            balance_items = temp
        if(not balance_items):
            return json_format(404, 'balanceitem is not found')
        balance_items_json = []
        for balance_item in balance_items:
            balance_items_json.append(balance_item.serialize())
        return json_format(200, 'balanceitem is found', ['balance_item'], balance_items_json) 

    @auth.login_required
    def post(self):
        balance_items_json = request.json['balance_item']
        if(balance_items_json is None):
            return json_format(400,'Invalid Request Error')
        user_id = db.session.query(User).filter_by(name = auth.username()).first().id
        if(isinstance(balance_items_json, dict)):
            temp = balance_items_json
            balance_items_json = dict()
            balance_items_json.append(temp)
        for balance_item_json in balance_items_json:
            balance_type = balance_item_json['balance_type']
            price = balance_item_json['price']
            image = balance_item_json['image']
            if(balance_type is None or price is None or image is None):
                return json_format(400, '')
            balance_item = BalanceItem(balance_type, price, image,user_id)
            db.session.add(balance_item)
        db.session.commit()
        return json_format(201, 'balanceitem is created', last_added_id = balance_item.id)

    @auth.login_required
    def put(self, id = None):
        user = db.session.query(User).filter_by(name = auth.username()).first()
        if(user is None):
            return json_format(401, 'unauthorized')
        balance_item_json = request.json['balance_item']
        balance_type = balance_item_json['balance_type']
        price = balance_item_json['price']
        image = balance_item_json['image']
        if(balance_type is None or price is None or image is None):
            return json_format(400, '')
        balance_item = None
        if(id is None):
            balance_item = BalanceItem(balance_type, price, image, user.id)
            db.session.add(balance_item)
            return json_format(200, 'balanceitem is created')
        for temp in user.balance_items:
            if(temp.id == id):
                balance_item = temp
                break
        if(balance_item is None):
            return json_format(404 ,'balance item is not found')
        balance_item.balance_type = balance_type
        balance_item.price = price
        balance_item.image = image
        db.session.commit()
        return json_format(200, 'balance_item is updated')
'''

class TestAPI(Resource):
    def get(self,num=None):
        if(num is None):
            return json_format(200,'yeah',['key1','key2'],[{'one':1,'two':2,'three':3},0])
        return json_format(200,'yeah',['key1','num'],[{'one':1,'two':2,'three':3},num])


api.add_resource(TestAPI,'/api/v1/test','/api/v1/test/<int:num>')
api.add_resource(UserAPI, '/api/v1/user', '/api/v1/users/<string:user_name>')
api.add_resource(WishListAPI, '/api/v1/wishlist','/api/v1/wishlist/<int:id>')
api.add_resource(ToDoAPI, '/api/v1/todo', '/api/v1/todo/<int:id>')
api.add_resource(HouseholdAccountsAPI, '/api/v1/household_accounts', '/api/v1/household_accounts/<int:id>')
#api.add_resource(BalanceListAPI, '/api/v1/balance_item', '/api/v1/balance_item/<int:id>')

if __name__=="__main__":
    app.run()

