# This file is part of askbot_fedmsg_plugin.
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

import fedmsg
import functools
import socket

fedmsg.init(name="askbot.%s" % socket.gethostname())

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

def fedmsg_callback(sender, topic=None, **kwargs):
    if 'signal' in kwargs:
        del kwargs['signal']

    import warnings
    import pprint
    kwargs['topic'] = topic
    warnings.warn(pprint.pformat(kwargs))

    if 'user' in kwargs:
        kwargs['agent'] = kwargs['user'].username
        del kwargs['user']

    if 'newly_mentioned_users' in kwargs:
        kwargs['newly_mentioned_users'] = [
            user.username for user in list(kwargs['newly_mentioned_users'])]

    if 'updated_by' in kwargs:
        kwargs['agent'] = kwargs['updated_by'].username
        del kwargs['updated_by']

    if 'delete_by' in kwargs:
        kwargs['agent'] = kwargs['delete_by'].username
        del kwargs['delete_by']

    if 'revision' in kwargs:
        kwargs['agent'] = kwargs['revision'].author.username
        print kwargs['revision'].post
        kwargs['revision'] = dict(
            (key, getattr(kwargs['revision'], key)) for key in (
                'tagnames', 'text', 'title', 'summary', 'pk',
            ))

    if 'post' in kwargs:
        kwargs['post'] = dict(
            (key, getattr(kwargs['post'], key)) for key in (
                'text', 'summary',
                'post_type', 'comment_count',
                'vote_up_count', 'vote_down_count', 'pk',
            ))

    if 'instance' in kwargs:
        kwargs['instance'] = dict(
            (key, getattr(kwargs['instance'], key)) for key in (
                'text', 'summary',
                'post_type', 'comment_count',
                'vote_up_count', 'vote_down_count', 'pk',
            ))
        #warnings.warn(serializers.serialize('json', [kwargs['post']], indent=2, use_natural_keys=True))

    warnings.warn(pprint.pformat(kwargs))
    fedmsg.publish(topic=topic, modname="askbot", msg=kwargs)

signals = {
    'tag.update': tags_updated,
    'post.edit': edit_question_or_answer,
    'post.delete': delete_question_or_answer,           # handled
    'post.flag_offensive.add': flag_offensive,
    'post.flag_offensive.delete': remove_flag_offensive,
    'user.update': user_updated,
    'user.new': user_registered,
    'post.edit': post_updated,
    'post.revision.publish': post_revision_published,
    #'site.visit': site_visited,
}
for topic, signal in signals.items():
    print topic, "->", signal
    signal.connect(functools.partial(fedmsg_callback, topic=topic), weak=False)


class NOOPMiddleware(object):
    """ Register our message-emitting plugin with django.

    Django middleware is supposed to provide a bunch of methods to act on the
    request/response pipeline.  We ignore that and instead use middleware as
    a convenient vector to get ourselves into the askbot runtime environment.

    """
    pass
