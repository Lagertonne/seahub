#from django.contrib.auth import get_user_model
from django.conf import settings
from xml.dom.minidom import parseString
#from django.contrib.auth.backends import ModelBackend
from seahub.auth.backends import RemoteUserBackend
from seahub.base.accounts import User
from seahub import auth
import crowd

import logging

logger = logging.getLogger(__name__)

#User = get_user_model()


class CrowdBackend(RemoteUserBackend):
    """
    This is the Attlasian CROWD (JIRA) Authentication Backend for Django
    Have a nice day! Hope you will never need opening this file looking for a bug =)
    """
    def authenticate(self, username, password):
        """
        Main authentication method
        """
        crowd_config = self._get_crowd_config()
        
        if not crowd_config:
            return None
        cs = crowd.CrowdServer(crowd_config['url'], crowd_config['app_name'], crowd_config['password'])
        resp = cs.auth_user(username, password)
        if resp is not None:
            try:
                user = User.objects.get(username)
                if (user.check_password(password) == False):
                    user.set_password(password)
                    user.save()
                    user = User.objects.get(username)
            except User.DoesNotExist:
                logger.error("Try to create a new user")
                user = self._create_new_user(username, password, resp)
        else:
            return None
        
        return user
        
    def _get_crowd_config(self):
        """
        Returns CROWD-related project settings. Private service method.
        """
        config = getattr(settings, 'CROWD', None)
        if not config:
            raise UserWarning('CROWD configuration is not set in your settings.py, while authorization backend is set')
        return config
    
    def get_user(self, username):
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            user = None
        return user

    def _find_existing_user(self, username):
        """
        Finds an existing user with provided username if one exists. Private service method.
        """
        users = User.objects.filter(username=username)
        if users.count() <= 0:
            return None
        else:
            return users[0]

    def _create_new_user(self, username, password, attribs):
        user = User.objects.create_user(username, password, is_active=True)
        user.first_name = attribs['first-name']
        user.last_name = attribs['last-name']
        return user
