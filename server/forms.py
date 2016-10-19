"""Forms for the web-facing portion of GMP3."""

from wtforms import Form, StringField, PasswordField, validators

class SearchForm(Form):
 search = StringField('Search', [validators.length(min = 1)])

class LoginForm(Form):
 username = StringField('username')
 password = PasswordField('password')
