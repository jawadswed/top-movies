from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField
from wtforms.validators import DataRequired
import requests
import os
from dotenv import load_dotenv

load_dotenv()

movie_db_api_key = os.getenv("MOVIE_DB_API_KEY")
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movie.db"
db.init_app(app)


# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    year: Mapped[str] = mapped_column(String(40), default="NAN", nullable=False)
    description: Mapped[str] = mapped_column(String(250), default="No Description", nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), default="Not Reviewed", nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    def __repr__(self):
        return f"{self.title}, {self.year}"


with app.app_context():
    db.create_all()


# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# second_movie = Movie(
#     title="Avatar The Way of Water",
#     year=2022,
#     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#     rating=7.3,
#     ranking=9,
#     review="I liked the water.",
#     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
# )
# with app.app_context():
#     db.session.add(second_movie)
#     db.session.commit()

class RateMovieForm(FlaskForm):
    rating = StringField(label="Enter the new rating")
    review = StringField(label="Enter the new review")
    submit = SubmitField('Done')


class AddMovieForm(FlaskForm):
    title = StringField(label="Enter the movie name", validators=[DataRequired()])
    submit = SubmitField(label="Search")


def find_movies(title):
    params = {"api_key": movie_db_api_key, "query": title}
    response = requests.get(MOVIE_DB_SEARCH_URL, params=params)
    data = response.json()["results"]
    return data


def find_movie_details(movie_id):
    params = {
        "api_key": movie_db_api_key,
    }
    response = requests.get(url=f"{MOVIE_DB_INFO_URL}/{movie_id}", params=params)
    data = response.json()
    return data


@app.route("/")
def home():
    movies = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars().all()
    for i in range(len(movies)):
        movies[i].ranking = len(movies) - i
    db.session.commit()
    return render_template("index.html", movies=movies)


@app.route("/edit/<movie_id>", methods=["GET", "POST"])
def rate_movie(movie_id):
    form = RateMovieForm()
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        if form.rating.data:
            movie.rating = float(form.rating.data)
        if form.review.data:
            movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template('edit.html', movie=movie, form=form)


@app.route("/delete/<movie_id>")
def delete(movie_id):
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        data = find_movies(movie_title)
        return render_template("select.html", movies_list=data)
    return render_template("add.html", form=form)


@app.route("/select/<int:movie_id>")
def add_movie_to_db(movie_id):
    data = find_movie_details(movie_id)
    new_movie = Movie(
        title=data["original_title"],
        year=data["release_date"].split("-")[0],
        description=data["overview"],
        img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('rate_movie', movie_id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
