from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField, PasswordField, SelectField, FieldList, FormField, Label, EmailField, DateField, IntegerField, TextAreaField
from wtforms.validators import InputRequired, Length, Email, NumberRange, ValidationError, Optional
# from email_validator import
import confg
from datetime import datetime


class LoginForm(FlaskForm):
    user_id = StringField('User name', validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField('Login')


class CreateForm(FlaskForm):
    user_id = StringField('User name', validators=[InputRequired(), Length(3, 20)])
    password = PasswordField("Password", validators=[InputRequired(), Length(3, 20)])
    mail = EmailField("Mail", validators=[InputRequired(), Email()])
    submit = SubmitField('Create account')


class AddGameForm(FlaskForm):
    name = StringField("Game name")
    submit = SubmitField('Create game')


class AddGameFieldForm(FlaskForm):
    new_field_name = StringField("Field name : ")
    new_field_value = StringField("Field value: ")
    submit = SubmitField('Add Field')


class GameInfoForm(FlaskForm):
    status = SelectField("Status", choices=confg.statuses)
    started_playing = DateField("Started playing")
    hours_played = IntegerField("Hours played")
    tags = TextAreaField("Tags")


class SteamAccountForm(FlaskForm):
    steam_link = StringField("Steam link", validators=[Optional(), InputRequired()])
    submit = SubmitField("add steam")


class AddCollection (FlaskForm):
    new_collection_name = StringField("New collection name", validators=[Optional(), InputRequired()])
    submit = SubmitField("New collection")

# class AllGameInfoForm(CriteriasForm):
# status = SelectField("Status", choices=confg.statuses)
# started_playing = DateField("Started playing", format='%d-%m-%Y')
