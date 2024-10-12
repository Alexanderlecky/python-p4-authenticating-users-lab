#!/usr/bin/env python3

from flask import Flask, jsonify, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, Article, User

app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)

# Resources

class ClearSession(Resource):
    def delete(self):
        # Clears all session data, including user_id and page_views
        session.clear()
        return jsonify({"message": "Session cleared"}), 204

class IndexArticle(Resource):
    def get(self):
        articles = [article.to_dict() for article in Article.query.all()]
        return jsonify(articles), 200

class ShowArticle(Resource):
    def get(self, id):
        session['page_views'] = 0 if not session.get('page_views') else session['page_views']
        session['page_views'] += 1

        if session['page_views'] <= 3:
            article = Article.query.filter(Article.id == id).first()
            if article:
                return jsonify(article.to_dict()), 200
            return jsonify({'error': 'Article not found'}), 404

        return jsonify({'message': 'Maximum pageview limit reached'}), 401

# User Authentication

class Login(Resource):
    def post(self):
        data = request.get_json()  # Expecting JSON payload
        username = data.get('username')

        # Find the user by username
        user = User.query.filter_by(username=username).first()

        if user:
            session['user_id'] = user.id  # Add user_id to session
            return jsonify({'message': f'Logged in as {user.username}', 'user_id': user.id}), 200
        return jsonify({'error': 'User not found'}), 404

class Logout(Resource):
    def post(self):
        if 'user_id' in session:
            session.pop('user_id')  # Remove user_id from session
            return jsonify({'message': 'Logged out successfully'}), 204  # No content, successful logout
        return jsonify({'error': 'No user logged in'}), 404

class CheckSession(Resource):
    def get(self):
        if 'user_id' in session:
            user_id = session['user_id']
            user = User.query.get(user_id)
            if user:
                return jsonify({'user_id': user_id, 'username': user.username}), 200
        return jsonify({'error': 'No active session'}), 401

# Add Resources to API

api.add_resource(ClearSession, '/clear')
api.add_resource(IndexArticle, '/articles')
api.add_resource(ShowArticle, '/articles/<int:id>')

# Add the user-related resources
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')

# Run the app

if __name__ == '__main__':
    app.run(port=5555, debug=True)
