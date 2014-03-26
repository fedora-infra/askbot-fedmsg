# This file is part of askbot_fedmsg.
# Copyright (C) 2013 Red Hat, Inc.
#
# fedmsg is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# fedmsg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with fedmsg; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
# Authors:  Ralph Bean <rbean@redhat.com>
#
""" Plugin to emit fedmsg messages from an askbot instance.

Enable this plugin by editing the ``settings.py`` file in your askbot
instance.

Find MIDDLEWARE_CLASSES and add 'askbot_fedmsg.NOOPMiddleware'
to the tuple like:

    MIDDLEWARE_CLASSES = (
        ...
        'askbot_fedmsg.NOOPMiddleware',
        ...
    )

"""


import fedmsg
import functools
import socket

hostname = socket.gethostname().split('.')[0]
fedmsg.init(name="askbot.%s" % hostname)

from django.core import serializers
import json

from django.dispatch import receiver

from askbot.models.signals import (
    tags_updated,
    edit_question_or_answer,
    delete_question_or_answer,
    flag_offensive,
    remove_flag_offensive,
    user_updated,
    user_registered,
    user_logged_in,
    post_updated,
    post_revision_published,
    site_visited,
)

from askbot.deps import django_authopenid


def username(user):
    """ Return the user's username...  *unless* that user logged in via FAS
    openid, in which case the FAS username is returned.
    """
    assocs = django_authopenid.models.UserAssociation.objects.filter(user=user)
    for association in assocs:
        url = association.openid_url
        if 'id.fedoraproject.org' in url:
            return url.split('://')[1].split('.')[0]

    # Otherwise
    return user.username


def mangle_kwargs(kwargs):
    """ Take kwargs as given to us by askbot and turn them into something that
    more closely resembles messages on the fedmsg bus.

    JSONify some django models.
    """

    if 'signal' in kwargs:
        del kwargs['signal']

    user_keys = ['user', 'mark_by', 'delete_by', 'updated_by']
    for key in user_keys:
        if key in kwargs:
            kwargs['agent'] = username(kwargs[key])
            del kwargs[key]

    if 'newly_mentioned_users' in kwargs:
        kwargs['newly_mentioned_users'] = [
            username(user) for user in list(kwargs['newly_mentioned_users'])]

    if 'revision' in kwargs:
        kwargs['agent'] = username(kwargs['revision'].author)
        kwargs['revision'] = dict(
            (key, getattr(kwargs['revision'], key)) for key in (
                'tagnames', 'text', 'title', 'summary', 'pk',
            ))
        kwargs['revision']['tagnames'] = \
            kwargs['revision']['tagnames'].split(' ')

    if 'post' in kwargs:
        kwargs['thread'] = kwargs['post'].thread
        kwargs['post'] = dict(
            (key, getattr(kwargs['post'], key)) for key in (
                'text', 'summary',
                'post_type', 'comment_count',
                'vote_up_count', 'vote_down_count', 'pk',
            ))

    if 'instance' in kwargs:
        kwargs['thread'] = kwargs['instance'].thread
        kwargs['instance'] = dict(
            (key, getattr(kwargs['instance'], key)) for key in (
                'text', 'summary',
                'post_type', 'comment_count',
                'vote_up_count', 'vote_down_count', 'pk',
            ))

    if 'thread' in kwargs:
        kwargs['topmost_post_id'] = kwargs['thread']._question_post().pk
        kwargs['thread'] = dict(
            (key, getattr(kwargs['thread'], key)) for key in (
                'tagnames', 'title', 'pk',
            ))
        kwargs['thread']['tagnames'] = \
            kwargs['thread']['tagnames'].split(' ')

    if 'tags' in kwargs:
        kwargs['tags'] = [tag.name for tag in kwargs['tags']]

    return kwargs


def fedmsg_callback(sender, topic=None, **kwargs):
    kwargs = mangle_kwargs(kwargs)
    fedmsg.publish(topic=topic, modname="askbot", msg=kwargs)

# Here is where we actually hook our callback up to askbot signals system
signals = {
    'tag.update': tags_updated,
    'post.edit': edit_question_or_answer,
    'post.delete': delete_question_or_answer,
    'post.flag_offensive.add': flag_offensive,
    'post.flag_offensive.delete': remove_flag_offensive,
    #'user.update': user_updated,
    #'user.new': user_registered,
    'post.edit': post_updated,
    #'post.revision.publish': post_revision_published,
    #'site.visit': site_visited,
}
for topic, signal in signals.items():
    signal.connect(functools.partial(fedmsg_callback, topic=topic), weak=False)


class NOOPMiddleware(object):
    """ Register our message-emitting plugin with django.

    Django middleware is supposed to provide a bunch of methods to act on the
    request/response pipeline.  We ignore that and instead use middleware as
    a convenient vector to get ourselves into the askbot runtime environment.

    """
    pass
