"""
    # Sample: https://flask.io/new
    pip install flask-bootstrap
    pip install flask-wtf
    pip install python-dotenv
    pip install flask_sqlalchemy
    pip install flask-login
    pip install mysqlclient
"""
from datetime import datetime
import shortuuid
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, BooleanField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import case
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import config

# ============================================================================
app = Flask(__name__)
app.config.from_object(config.conf)

Bootstrap(app)
csrf = CSRFProtect(app)

# ============================================================================
# Connect to Database
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    """ User Register Form """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

    addresses = db.relationship('List', backref='users', lazy=True)

class List(db.Model):
    """
        To-do List TABLE Configuration. 

        url_key: a key to link user and lists
        ForiegnKey: user_id
    """
    __tablename__ = "lists"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url_key = db.Column(db.String(250), nullable=False, unique=True)
    name = db.Column(db.String(250), nullable=False, unique=False)
    created_date = db.Column(db.String(250), nullable=False, unique=False)
    task_cnt = db.Column(db.String(20), nullable=False, unique=False)
    archive = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    addresses = db.relationship('Task', backref='lists', lazy=True)
    addresses = db.relationship('User', backref='lists', lazy=True)

    def to_dict(self):
        """
            Package all items into a dict in order to more convinient usage afterward.
            For loop and save all columns into a dict, return this dict
        """
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    def __repr__(self):
        """Preset the key info to be printed"""
        return f"List: <{self.id}, {self.name}, {self.url_key}, {self.user_id}>"

class Task(db.Model):
    """
        Task TABLE Configuration. 
        ForiegnKey: list_id
    """
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(250), unique=False, nullable=False)
    due_date = db.Column(db.String(100), nullable=True) # format: "%Y-%m-%d %H:%M:%S"
    status = db.Column(db.Boolean)
    favorit = db.Column(db.Boolean, nullable=True)
    list_id = db.Column(db.Integer, db.ForeignKey('lists.id'), nullable=False)

    addresses = db.relationship('List', backref='tasks', lazy=True)

    def to_dict(self):
        """
            Package all items into a dict in order to more convinient usage afterward.
            For loop and save all columns into a dict, return this dict
        """
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    def __repr__(self):
        """Preset the key info to be printed"""
        return f"Card: <{self.id}, {self.name}, {self.due_date}, {self.status}, {self.favorit}, {self.list_id}>"


# Create table:
with app.app_context():
    db.create_all()

# ============================================================================
class RegisterForm(FlaskForm):
    """
        User to register an account to access Task Management Sysytem.
        Infomation will be saved to the user table:
            - email
            - password
            - name
    """
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("SIGN ME UP!")

class LoginForm(FlaskForm):
    """
        User to login to the Task Management Sysytem.
    """
    email = StringField(label='Email', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField(label="Log In")

class ListForm(FlaskForm):
    """
        Add a new list under a existing board.
    """
    name = StringField(label='List name', validators=[DataRequired()])
    favorit = BooleanField(label="☆")
    submit = SubmitField(label='Submit')

class TaskForm(FlaskForm):
    """
        Add a new task to a existing list
    """
    name = StringField(label='Title:', validators=[DataRequired()])
    due_date = StringField(label='Due Date:')
    status = BooleanField(label="Status:")
    favorit = BooleanField(label="☆")
    submit = SubmitField(label='Submit')

# ============================================================================
@login_manager.user_loader
def load_user(user_id):
    """Load user's information"""
    return User.query.get(user_id)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
        User Registration
        - Flash error messages when there's a existing account
        - Login user after the registration
    """
    form = RegisterForm()
    if form.validate_on_submit():
        email = request.form.get('email')
        with app.app_context():
            if db.session.query(User).filter(User.email == request.form.get('email')).first():
                flash(f"An account is alredy signed up with \"{email}\"\nplease try other email address or move to login page instead.")
            else:
                hash_and_salt_pw = generate_password_hash(
                    password = request.form.get("password"),
                    method = 'pbkdf2:sha256',
                    salt_length = 8
                )
                new_user = User(
                    email = request.form.get('email'),
                    password = hash_and_salt_pw,
                    name = request.form.get('name')
                )
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)  
                flash("✓ Signed in successfully", "success")      
                return redirect(url_for('mylists'))
    return render_template('register.html', form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    """
        User Log in to the system
        - Flash error message when the email address not found, or password is wrong
        - Redirect to 'lists.html' page after login
    """
    form = LoginForm()
    with app.app_context():
        if form.validate_on_submit():
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            print(f'User entered pw: {password}(tyle: {type(password)})')
            if not user:
                flash("Email not found, please try again.")
                return redirect(url_for('login'))
            elif not check_password_hash(user.password, password):
                flash("❗️ Password incorrect, please try again.", "error")
                print(f'The correct pw: {user.password}(tyle: {type(user.password)})')
                return redirect(url_for('login'))
            else:
                login_user(user)
                flash("✓ Signed in successfully", "success")
                return redirect(url_for('mylists'))
    return render_template("login.html", form=form)


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    """Log out and back to the home page"""
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for('home'))

# =======================================================
@app.route("/", methods=["GET"])
def home():
    """The top page of To-do Manager before Login"""
    return render_template('index.html')

@app.route("/my_lists", methods=["GET"])
def mylists():
    """
        The Top page of To-do Manager after login
        - Listing up all existing To-do Lists of this user
        - Each To-do List can be deleted or clicked to check all linked Tasks in it
        
    """
    with app.app_context():
        my_lists = db.session.query(List).filter(List.user_id == current_user.id, List.archive == False).all()
        print(f'current user id: {current_user.id}, lists: {my_lists}')
    return render_template("lists.html", all_list=my_lists)

@app.route("/new_list", methods=["GET", "POST"])
@login_required
def new_list():
    """
        Create a new To-do list
        The default list name may add a symbol when there're duplicates
        eg. New list 2024-05-29 (1)
    """
    date = datetime.today().strftime('%Y-%m-%d')
    time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    day_of_week = datetime.today().strftime('%a')
    l_name = f"To-do list :  {date} ({day_of_week})"

    with app.app_context():   
        url_key = shortuuid.ShortUUID().random(length=10)
        exist_lists = db.session.query(List).filter(
            List.user_id == current_user.id, 
            List.name.like(l_name + "%"), 
            List.created_date.like(date + "%")
        ).all()
        if len(exist_lists) > 0:
            l_name += f'({len(exist_lists)})'
        user_id = current_user.id
        n_list = List(name = l_name, url_key = url_key, created_date=time, task_cnt="0", archive=False, user_id=user_id)
        db.session.add(n_list)
        db.session.commit()
        flash(f'A new list: {l_name} created!', "success")
        print(f"New list created: {n_list}. Click the pencil mark to change list name.")
        return redirect(url_for("new_task", url_key=url_key))

@app.route("/edit_name/<url_key>", methods=["GET", "POST"])
def edit_l_name(url_key):
    """Allow user to change list name"""
    with app.app_context():
        p_list = db.session.query(List).filter(List.url_key == url_key).first()
        if request.method == "POST":
            new_name = request.form['new-name']
            p_list.name = new_name
            db.session.commit()
            flash("✓ List's name has been updated!", "success")
            print(f"{p_list.id}'s name has been updated to: {new_name}")
    return redirect(url_for("new_task", url_key=url_key))

@app.route('/archive/<url_key>', methods=["GET", "POST"])
@login_required
def archive_list(url_key):
    """Allow user to archive a list to database"""
    with app.app_context():
        p_list = db.session.query(List).filter(List.url_key == url_key).first()
        if p_list.archive == True:
            p_list.archive = False
            flash(f'"{p_list.name}" has been unarchived! you can check it in your "Mylists".', 'success')
        else:
            p_list.archive = True
            flash(f'"{p_list.name}" has been archived!', 'success')
        db.session.commit()
        return redirect(url_for('mylists'))

@app.route("/del/<url_key>", methods=["GET", "POST"])
def del_list(url_key):
    """Allow uer to delete a list from mylists page"""
    with app.app_context():
        d_list = db.session.query(List).filter(List.url_key == url_key).first()
        if d_list:
            d_tasks = db.session.query(Task).filter(Task.list_id == d_list.id).all()
            for task in d_tasks:
                db.session.delete(task)
                db.session.commit()
            db.session.delete(d_list)
            db.session.commit()
            flash(f'✓ "{d_list.name}" deleted successfully!', "success")
        else:
            flash(f'❗️"{d_list.name}" not found', "error")
    with app.app_context():
        p_list = db.session.query(List).filter(List.user_id == current_user.id).all()[::-1][0]
        p_url_key = p_list.url_key
        db.session.commit()
        return redirect(url_for('new_task', url_key=p_url_key))
    
# =======================================================   
@app.route('/task/<url_key>', methods=["GET", "POST"])
def new_task(url_key):
    """Create a New Task without log-in"""
    task_form = TaskForm()
    t_name = request.form.get('name')
    with app.app_context():
        all_list = db.session.query(List).filter(List.user_id == current_user.id).all()
        p_list = db.session.query(List).filter(List.url_key == url_key).first()
        if t_name:
            duplicate = db.session.query(List, Task).filter(List.url_key == url_key, Task.name.like(t_name + "%")).all()
            if len(duplicate) > 0:
                t_name = f'{t_name}({len(duplicate)})'
        if task_form.validate_on_submit():
            n_task = Task(
                name = t_name,
                list_id = p_list.id,
                )
            db.session.add(n_task)
            db.session.commit()
            print(f"New card submitted: {n_task}")
            flash("✓ Great, a new task created. you can add a due date or mark it as favorit.", "success")
    
        status_case = case((Task.status == True, 1), (Task.status == False, 0))
        favorit_case = case((Task.favorit == True, 1), (Task.favorit == False, 0))
        due_date_case = case((Task.due_date == None, 1), (Task.due_date != None, 0))
        p_task = db.session.query(Task).filter(Task.list_id == p_list.id).order_by(
            status_case.desc(),
            favorit_case.asc(),
            due_date_case.desc(),
            Task.due_date.desc()
        ).all()
        p_list.task_cnt = len(p_task)
        db.session.commit()
        print(len(p_task), p_task)
        return render_template('tasks.html', all_list=all_list, form=task_form, list=p_list, url_key=url_key, all_task=p_task)

@app.route("/edit_task_name/<url_key>/<id>", methods=["GET", "POST"])
def edit_t_name(url_key, id):
    """Allow user to change task name"""
    print(f'task_id = {id}')
    with app.app_context():
        task = db.session.query(Task).filter(Task.id == id).first()
        print(f"被选中修改名称的 task: {task.name}")
        task.name = request.form['new-t-name']
        db.session.commit()
        flash("✓ Task's name has been updated!", "success")
        print(f"{task.id}'s name has been updated to: {task.name}")
        return redirect(url_for("new_task", url_key=url_key))

@app.route("/date/<url_key>/<id>", methods=["GET", "POST"])
def new_date(url_key, id):
    """Allow user to add task due date"""
    with app.app_context():
        task = db.session.query(Task).filter(Task.id == id).first()
        task.due_date = request.form['due_date']
        db.session.commit()
        flash(f'✓ Due date of task: "{task.name}" has been added!', 'success')
        return redirect(url_for('new_task', url_key=url_key))

@app.route("/complete/<url_key>/<id>", methods=["GET", "POST"])
def complete(url_key, id):
    """Allow user to change status of task"""
    with app.app_context():
        task = db.session.query(Task).filter(Task.id == id).first()
        if task.status:
            task.status = False
            flash(f'Status of task: "{task.name}" has been changed!', 'success')
        else:
            task.status = True
            flash(f'Status of task: "{task.name}" has been changed to completed!', 'success')
        db.session.commit()
    with app.app_context():
        p_list = db.session.query(List).filter(List.url_key == url_key).first()
        all_tasks = db.session.query(Task).filter(Task.list_id == p_list.id).all()
        completed_tasks = [task for task in all_tasks if task.status]
        print(f'list:{p_list.name} has {len(all_tasks)} tasks, now finished {len(completed_tasks)} tasks.')
        if len(all_tasks) == len(completed_tasks):
            flash('All tasks finished! Good job!', 'success')
        db.session.commit()    
    return redirect(url_for('new_task', url_key=url_key))

@app.route("/favorit/<url_key>/<id>", methods=["GET", "POST"])
def check_favorit(url_key, id):
    """Allow user to star a task"""
    with app.app_context():
        task = db.session.query(Task).filter(Task.id == id).first()
        if task.favorit:
            task.favorit = False
            flash(f'Task: "{task.name}" has been unstarred!', 'success')
        else:
            task.favorit = True
            flash(f'Task: "{task.name}" has been starred!', 'success')
        db.session.commit()
        return redirect(url_for('new_task', url_key=url_key))

@app.route("/del/<url_key>/<id>", methods=["GET", "POST"])
def del_task(url_key, id):
    """Allow user to delete a task"""
    with app.app_context():
        task = db.session.query(Task).filter(Task.id == id).first()
        db.session.delete(task)
        db.session.commit()
        flash(f'Task: "{task.name}" has been deleted!', 'success')
        return redirect(url_for('new_task', url_key=url_key))

@app.route("/copy/<url_key>", methods=["GET", "POST"])
def copy_list(url_key):
    """
        Copy a exist To-do list along with all tasks under it;
        list name format: name of exist list (copy)
        Different points: 
            - url_key
            - list id, list name, create date
            - task id
    """
    new_url_key = shortuuid.ShortUUID().random(length=10)
    time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    with app.app_context():
        p_list = db.session.query(List).filter(List.url_key == url_key).first()
        l_name = f"{p_list.name} (copy)"
        n_list = List(name = l_name, url_key = new_url_key, created_date=time, task_cnt=p_list.task_cnt, archive=False, user_id=current_user.id)
        db.session.add(n_list)
        db.session.commit()
    with app.app_context():
        p_list = db.session.query(List).filter(List.url_key == url_key).first()
        all_tasks = db.session.query(Task).filter(Task.list_id == p_list.id).all()

        n_list = db.session.query(List).filter(List.url_key == new_url_key).first()
        for copy_task in all_tasks:
            n_task = Task(
                name = copy_task.name,
                due_date = copy_task.due_date,
                status = copy_task.status,
                favorit = copy_task.favorit,
                list_id = n_list.id,
                )
            db.session.add(n_task)
            db.session.commit()
        flash('✓ List copied successfully! Click the pencil mark to change list name.', "success")
        return redirect(url_for("new_task", url_key=new_url_key))

# ============================================================================
if __name__ == '__main__':
    app.run()