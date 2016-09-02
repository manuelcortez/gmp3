"""Pyglet validator for use with config.py."""

from simpleconf.validators import ValidationError, Boolean

class PygletValidator(Boolean):
 def validate(self, option):
  super(PygletValidator, self).validate(option)
  if option.value:
   try:
    import pyglet
    assert pyglet
   except (ImportError, AssertionError):
    raise ValidationError('Pygame is not installed.')
