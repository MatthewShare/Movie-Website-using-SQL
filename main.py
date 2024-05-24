from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
Bootstrap5(app)
API_KEY = API_KEU
URL = "https://api.themoviedb.org/3/search/movie"
URL_DETAILS = "https://api.themoviedb.org/3/movie/"
IMAGE_URL = "https://image.tmdb.org/t/p/original/"


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"

db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=True)


class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g 7.5")
    review = StringField("Your Review")
    button = SubmitField("Done")


class AddFilmForm(FlaskForm):
    title = StringField("Movie Title")
    button = SubmitField("Submit")


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    movies = db.session.query(Movie).order_by(Movie.rating).all()[::-1]
    for movie in movies:
        movie.ranking = movies.index(movie) + 1
    return render_template("index.html", movies=movies)


@app.route("/edit", methods=["GET", "POST"])
def update():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie_to_edit = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        new_rating = float(form.rating.data)
        new_review = form.review.data
        movie_to_edit.rating = new_rating
        movie_to_edit.review = new_review
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie=movie_to_edit, form=form)


@app.route('/delete')
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=["GET", "POST"])
def add():
    add_form = AddFilmForm()
    if add_form.validate_on_submit():
        title = add_form.title.data
        response = requests.get(URL, params={"api_key": API_KEY, "query": title})
        selects = response.json()["results"]
        return render_template('select.html', movies=selects)
    return render_template("add.html", form=add_form)


@app.route('/add_data', methods=["GET", "POST"])
def add_data():
    movie_id = request.args.get("id")
    response = requests.get(f"{URL_DETAILS}/{movie_id}", params={"api_key": API_KEY})
    title = response.json()["title"]
    year = response.json()["release_date"].split('-')[0]
    description = response.json()["overview"]
    poster_path = response.json()["poster_path"]
    image_url = f"{IMAGE_URL}{poster_path}"
    new_movie = Movie(title=title, year=year, description=description, img_url=image_url)
    db.session.add(new_movie)
    db.session.commit()
    database_id = new_movie.id
    return redirect(url_for('update', id=database_id))


if __name__ == '__main__':
    app.run(debug=True)
