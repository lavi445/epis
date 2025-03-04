from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for, request, flash, Flask, render_template
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_admin.form.upload import ImageUploadField
import os

from models import db, Event, User

# Define upload folder for event images
UPLOAD_FOLDER = os.path.join(os.getcwd(), "static/uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = "admin.login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Custom Admin View with Authentication
class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for("admin.login"))
        return super().index()

class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("admin.login"))

# Custom Event Admin View to handle image uploads and registration link
class EventAdmin(SecureModelView):
    form_overrides = {"image": ImageUploadField}
    form_extra_fields = {
        "image": ImageUploadField(
            "Event Image",
            base_path=UPLOAD_FOLDER,  # Where images are stored
            url_relative_path="uploads/",  # URL path for accessing images
            namegen=lambda obj, file_data: secure_filename(file_data.filename)  # Secure filename
        )
    }

    # Define which columns are editable in Flask-Admin
    form_columns = ['title', 'date', 'time', 'venue', 'registration_fees', 'description', 'image', 'rules', 'registration_link']

# Initialize Flask-Admin
admin = Admin(index_view=MyAdminIndexView())

def setup_admin(app):
    admin.init_app(app)
    login_manager.init_app(app)
    
    admin.add_view(EventAdmin(Event, db.session))  # Register Event model with the admin panel
    
    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if current_user.is_authenticated:
            return redirect(url_for("admin.index"))
        
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            user = User.query.filter_by(username=username).first()

            if user and check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for("admin.index"))
            else:
                flash("Invalid credentials!", "danger")

        return render_template("admin_login.html")

    @app.route("/admin/logout")
    @login_required
    def admin_logout():
        logout_user()
        return redirect(url_for("admin.login"))
