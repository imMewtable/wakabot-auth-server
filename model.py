import os
from dotenv import load_dotenv
from peewee import *
from playhouse.mysql_ext import MySQLDatabase

load_dotenv('secrets.env')
HOST = os.getenv('MYSQL_HOST')
MYSQL_USERNAME = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
DB_NAME = os.getenv('MYSQL_DATABASE_NAME')

db = MySQLDatabase(
    host=HOST,
    user=MYSQL_USERNAME,
    password=MYSQL_PASSWORD,
    database=DB_NAME
)


class BaseModel(Model):
    """A base model that will use our MySQL database."""
    class Meta:
        database = db


class WakaData(BaseModel):
    discord_username = CharField(null=False, max_length=40)
    wakatime_username = CharField(null=True, max_length=40)
    auth_token = CharField(null=True, max_length=100)
    refresh_token = CharField(null=True, max_length=100)
    server_id = BigIntegerField(null=False)

    class Meta:
        primary_key = CompositeKey('discord_username', 'server_id')


class AuthenticationState(BaseModel):
    discord_username = CharField(null=False, max_length=40)
    server_id = BigIntegerField(null=False)
    state = CharField(null=False, max_length=50)

    class Meta:
        primary_key = CompositeKey('discord_username', 'server_id')


def get_user(discord_username):
    db.connect(reuse_if_open=True)
    data = WakaData.get(WakaData.discord_username == discord_username)
    db.close()
    return data.server_id


def state_exists(state):
    """
    Checks the AuthenticationState table to see if the state exists.
    Used to verify the identity for the token authorization URL
    :param state: the state passed in that will be compared to the DB
    :return: True if the state exists, False if not.
    """
    try:
        db.connect(reuse_if_open=True)
        data = AuthenticationState.get(AuthenticationState.state == state)
        if data.discord_username and data.server_id:
            db.close()
            return True
        else:
            db.close()
            return False

    except Exception as e:
        print(e)
        db.close()
        return False


def get_user_data_from_state(state):
    """
    Retrieves the data that is associated with each state in the database.
    :param state: the state used in the OAuth parameter
    :return: The data associated with the state in the AuthenticationState database, or None if it doesn't exist
    """
    try:
        db.connect(reuse_if_open=True)
        data = AuthenticationState.get(AuthenticationState.state == state)
        db.close()
        return data
    except Exception as e:
        print(e)
        db.close()
        return None


def create_user_data(discord_username, wakatime_username, auth_token, refresh_token, server_id):
    """
    Initializes user data from parameters in the WakaData table
    :param discord_username: the discord username as a string (ie, 'john#1234')
    :param wakatime_username: the wakatime username of the user. Can be None/Null if user didn't create account
    :param auth_token: The access token given by the wakatime token API to make authenticated API calls
    :param refresh_token: The refresh token given by the wakatime token API to get new access tokens
    :param server_id: The bigint server ID that the discord_username registered with
    :return: An int representing how many changes were made in the database. 1 is a successful insert.
    """
    db.connect(reuse_if_open=True)

    code = WakaData.create(discord_username=discord_username,
                           server_id=server_id,
                           wakatime_username=wakatime_username,
                           auth_token=auth_token,
                           refresh_token=refresh_token)
    db.close()
    return code
