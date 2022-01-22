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
    """A base model that will use our Sqlite database."""
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


def state_exists(state):
    try:
        db.connect(reuse_if_open=True)
        data = AuthenticationState.get(AuthenticationState.state == state)
        if data.discord_username and data.server_id:
            return True
        else:
            return False

    except Exception as e:
        print(e)
        db.close()
        return False


def get_user_data_from_state(state):
    try:
        db.connect(reuse_if_open=True)
        data = AuthenticationState.get(AuthenticationState.state == state)
        return data
    except Exception as e:
        print(e)
        db.close()
        return None


def create_user_data(discord_username, wakatime_username, auth_token, refresh_token, server_id):
    db.connect(reuse_if_open=True)

    code = WakaData.create(discord_username=discord_username,
                           server_id=server_id,
                           wakatime_username=wakatime_username,
                           auth_token=auth_token,
                           refresh_token=refresh_token)
    db.close()
    return code