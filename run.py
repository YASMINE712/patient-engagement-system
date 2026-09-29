"""Start the local development server: python run.py."""
from health_friend.web import app

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=False)
