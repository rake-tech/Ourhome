from ourhome_app import app, initialize_database


if __name__ == "__main__":
    with app.app_context():
        initialize_database()
    app.run(debug=False, use_reloader=False)

