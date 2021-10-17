from pprint import pprint

from django.db import models
from stregsystem.models import Member
from treo.settings import cfg


class Movie(models.Model):
    id = models.CharField(
        max_length=16, primary_key=True, help_text="IMDB/TMDB id of movie (e.g. Pulp Fiction tt0110912)"
    )
    title = models.CharField(max_length=128, blank=True)
    original_title = models.CharField(max_length=128, null=True, blank=True)  # omit from view if equal or null
    release_date = models.DateField(null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    poster = models.ImageField(null=True, blank=True)
    avg_rating = models.FloatField(null=True, blank=True, help_text="average rating given by movie API")

    def __str__(self):
        if self.release_date and self.title:
            return f"{self.title}{' (' + str(self.release_date.year) + ')' if self.release_date else ''}"
        if self.title:
            return self.title
        else:
            return f"movie_id: {self.id}"

    @staticmethod
    def create_from_id(m_id):
        from tmdbv3api import TMDb, exceptions, Movie as TMDbMovie

        tmdb = TMDb()
        tmdb.api_key = cfg.get("tmdb", "API_KEY")
        tmdb.language = 'en'
        tmdb_movie = TMDbMovie()

        try:
            m = tmdb_movie.details(movie_id=m_id)
        except exceptions.TMDbException:
            return RuntimeError("TMDb lookup failed although ID was verified earlier")

        return Movie.objects.create(
            id=m_id,
            title=m.title,
            summary=m.overview,
            original_title=m.original_title,
            release_date=m.release_date,
            avg_rating=m.vote_average,
        )


class Season(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()

    @property
    def season_str(self):
        return f"{'Spring' if self.start_date.month <= 6 else 'Fall'} {self.start_date.year}"

    def __str__(self):
        return self.season_str


class Event(models.Model):
    event_date = models.DateField(blank=True, null=True)
    theme = models.CharField(max_length=128)
    movies = models.ManyToManyField(Movie, help_text="pair of movies for the event")  # todo; add select2 to this field
    proposer = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="proposer of event, given as fklub member to derive name",
    )  # todo add select2 only for admin
    votes = models.IntegerField(default=0, help_text="number of fkult votes received on season initiation")
    accepted = models.BooleanField(blank=True, null=True, help_text="accepted at fkult season initiation")
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        if self.proposer:
            return f"{self.theme} by {self.proposer.firstname} {self.proposer.lastname} was {'not' if not self.accepted else ''} accepted"
        else:
            return self.theme