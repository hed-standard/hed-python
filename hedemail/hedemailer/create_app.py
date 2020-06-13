from hedemailer.app_factory import AppFactory

app = AppFactory.create_app('config.Config')
with app.app_context():
    from hedemailer.routes import route_blueprint
    app.register_blueprint(route_blueprint)
