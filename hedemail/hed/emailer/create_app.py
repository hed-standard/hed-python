from hed.emailer.app_factory import AppFactory

app = AppFactory.create_app('config.Config')
with app.app_context():
    from hed.emailer.routes import route_blueprint
    app.register_blueprint(route_blueprint)
