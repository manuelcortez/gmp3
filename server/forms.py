"""Forms for the web-facing portion of GMP3."""

from wtforms import Form, StringField, validators

class SearchForm(Form):
 search = StringField('Search', [validators.length(min = 1)])
