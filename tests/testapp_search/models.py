"""Models the search tests index: one a request may filter, one never indexed."""

from django.db import models
from modelsearch import index


class Note(index.Indexed, models.Model):
    """An indexed record with a visibility flag modelsearch does not index."""

    title = models.CharField(max_length=100)
    body = models.TextField(blank=True)
    public = models.BooleanField(default=True)

    search_fields = [
        index.SearchField("title"),
        index.SearchField("body"),
        index.AutocompleteField("title"),
        index.FilterField("id"),
    ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f"/notes/{self.pk}/"


class PlainNote(models.Model):
    """A record that is not indexed at all."""

    title = models.CharField(max_length=100)
