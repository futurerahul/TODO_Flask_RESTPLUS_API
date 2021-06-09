from flask import Flask
from flask.globals import request
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_restplus import Api, Resource, fields

# from flask_marshmallow import base_fields

# from flask_restplus import PostFormParameters

from sqlite3 import Connection as SQLite3Connection
from sqlalchemy import event
from sqlalchemy.engine import Engine

from datetime import datetime

app = Flask(__name__)
api = Api(app)
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Database config settings -- sqlite in this case
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sqlite.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# to enforce foreign key constraint in sqlite3
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


class Todo(db.Model):

    __tablename__ = "todo"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    complete = db.Column(db.Boolean, default=False)
    created = db.Column(db.DateTime)


# Serializer (Python object --> JSON and vice-verse)
class TodoSchema(ma.Schema):
    class Meta:
        fields = ("id", "title", "complete", "created")


todo_schema = TodoSchema()
todos_schema = TodoSchema(many=True)

# Input arguments (Parameters) for Todo
# class CreateTodoParameters(PostFormParameters):
#     title = base_fields.String(description="Example: Todo Title", required=True)

#     class Meta(TodoSchema.Meta):
#         fields = ("title",)

todo_fields = api.model("Todo", {"title": fields.String})

marshal_fields = api.model(
    "Todo",
    {"title": fields.String, "complete": fields.Boolean, "created": fields.DateTime},
)


@api.route("/tasks")
class TaskList(Resource):
    @api.marshal_with(
        marshal_fields
    )  # return only the marshal fields using this decorator
    def get(self):
        tasks = Todo.query.all()
        return todos_schema.dump(tasks), 200

    @api.expect(todo_fields)  # provide same functionality as PostFormParameters
    def post(self):
        payload = request.get_json()
        now = datetime.now()
        new_task = Todo(title=payload["title"], created=now)
        db.session.add(new_task)
        db.session.commit()

        return {"message": "task created"}, 201
        # new_task = todo_schema.load(api.payload)

        # return {"message": "task created"}, 201


@api.route("/tasks/<task_id>")
class Task(Resource):
    def get(self, task_id):
        task = Todo.query.filter_by(id=task_id).first()
        if task is None:
            return {"Error": "No task with input ID"}, 400

        return todo_schema.dump(task), 200

    def put(self, task_id):
        current_task = Todo.query.filter_by(id=task_id).first()
        if current_task is None:
            return {"Error": "No task with input ID"}, 400

        current_task.complete = not current_task.complete
        db.session.commit()
        return {"message": "task updated"}, 201

    def delete(self, task_id):
        task = Todo.query.filter_by(id=task_id).first()
        if task is None:
            return {"Error": "no task by input id"}

        db.session.delete(task)
        db.session.commit()
        return {"message": "task deleted"}, 201


if __name__ == "__main__":
    app.run(debug=True)
