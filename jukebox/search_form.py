"""Provides the search form class."""

from wtforms import Form, StringField

class SearchForm(Form):
    """Enables searching for tracks."""
    
    search = StringField('Search for')
