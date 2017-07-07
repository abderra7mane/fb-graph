#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
from urlparse import urlparse, parse_qs
import requests


FB_GRAPH_URL = 'https://graph.facebook.com/{version}/{node}'
FB_GRAPH_VERSIONS = ['2.2', '2.3', '2.4', '2.5', '2.6', '2.7', '2.8']
FB_GRAPH_DEFAULT_VERSION = FB_GRAPH_VERSIONS[-1]


def is_iterable(obj):
    return (isinstance(obj, list) or 
            isinstance(obj, tuple))


class FBGraphError(Exception):
    """
    """
    
    def __init__(self, error):
        self.code = None
        self.type = None

        try:
            self.message = error['error']['message']
            self.code = error['error']['code']
            self.type = error['error']['type']
        except:
            self.message = str(error)
        
        super(FBGraphError, self).__init__(self.message)


class FBGraph(object):
    """
    Facebook Graph API.
    """

    def __init__(self, access_token,
                       session=requests.Session(), 
                       version=FB_GRAPH_DEFAULT_VERSION):
        super(FBGraph, self).__init__()

        self.access_token = access_token
        self.version = version
        self.session = session

    def setAccessToken(self, access_token):

        self.access_token = access_token

    def get(self, node, params=None, version=None):
        """
        Request the given graph node and return
        the requested data.

        parameters
            node        Facebook Graph node to request.
            
            params      Query parameters to pass along 
                        with the request.

                        Mandatory parameters include:
                            access_token
        """

        if params is None:
            params = dict()
        
        if 'access_token' not in params:
            params['access_token'] = self.access_token
        
        params['format'] = 'json'

        if version is None:
            version = self.version

        version = 'v' + version

        url = FB_GRAPH_URL.format(version=version, 
                                  node=node)

        result = None
        
        has_next = True

        while has_next:

            try:
                response = self.session.get(url, params=params)
                _response = response.json()

                if _response.has_key('paging'):

                    if result is None:
                        result = _response
                    
                    else:
                        data = _response['data']
                        result['data'].extend(data)

                    paging = _response['paging']

                    if paging.has_key('next'):

                        _next = paging['next']
                        params = parse_qs(urlparse(_next).query)

                        continue
                
                elif not result:
                    result = _response

                if result.has_key('paging'):
                    del result['paging']

                has_next = False
            
            except requests.ConnectionError:
                
                raise FBGraphError(
                    "Failed to establish a connection "
                    "to the host.")
            
            except requests.RequestException as e:
                raise FBGraphError(e)

        if result.has_key('error'):

            raise FBGraphError(result)

        return result

    def _get_node_field(self, node, field, **kwargs):
        """
        Retrieve one field value from one node.
        """
        params = kwargs.pop('params', dict())
        params['fields'] = field

        response = self.get(node, params, **kwargs)

        if response.has_key('data'):
            return response['data']

        else:
            return response

    def _get_node_fields(self, node, fields, **kwargs):
        """
        Retrieve the values of multiple fields from one node.
        """

        if len(fields) == 1:
            return self._get_node_field(node, fields[0], **kwargs)

        _fields = ','.join(fields)

        params = kwargs.pop('params', dict())
        params['fields'] = _fields
        
        response = self.get(node, params=params, **kwargs)

        if response.has_key('data'):
            return response['data']

        else:
            return response

    def _get_nodes_field(self, nodes, field, **kwargs):
        """
        Retrieve the value of one field from multiple nodes.
        """

        path = '/'
        ids = ','.join(nodes)

        params = kwargs.pop('params', dict())
        params['ids'] = ids
        params['fields'] = field

        response = self.get(path, params=params, **kwargs)
        
        return response

    def _get_nodes_fields(self, nodes, fields, **kwargs):
        """
        Retrieve the values of multiple fields from multiple nodes.
        """

        if len(nodes) == 1:
            return self._get_node_fields(nodes[0], fields, **kwargs)

        if len(fields) == 1:
            return self._get_nodes_field(nodes, fields[0], **kwargs)

        path = '/'
        ids = ','.join(nodes)
        _fields = ','.join(fields)

        params = kwargs.pop('params', dict())
        params['ids'] = ids
        params['fields'] = _fields

        response = self.get(path, params=params, **kwargs)

        return response

    def get_fields(self, nodes, fields, **kwargs):
        """
        Retrieve the values of one or multiple fields from 
        one or multiple nodes.

        parameters
            nodes       The graph node ID or a list of nodes IDs.

            fields      The field name to be requested or a list 
                        of field names.
            
            kwargs      keyword args to be passed to get() function.
                        [see: get() function definition]

        return
            A dict mapping the different fields name to their values 
            or a list of dict if multiple nodes where requested.
        """
        if is_iterable(nodes):
            
            if is_iterable(fields):
                
                return self._get_nodes_fields(
                        nodes, fields, **kwargs)
            
            else:
                return self._get_nodes_field(
                        nodes, fields, **kwargs)
        else:
            
            if is_iterable(fields):
                
                return self._get_node_fields(
                        nodes, fields, **kwargs)
            
            else:
                return self._get_node_field(
                        nodes, fields, **kwargs)

    def get_uid(self):
        """
        Retrieve the current user id.
        """

        return self.get_fields('me', 'id')['id']

    def get_user_info(self, node='me', fields=['id', 'name']):
        """
        Retrieve some basic information about the user 
        whose id is given by node parameter.
        """

        #### fake response
        # return {'id': '1234569870', 'name': 'Milanov Leovol'}

        return self.get_fields(node, fields)

    def get_user_picture_url(self, node='me'):
        """
        Retrieve the profile picture url for the user whose
        id is given by the node parameter.
        """

        #### fake response
        # return 'https://www.facebook.com/photo.png'

        params = dict(type='large', redirect='false')

        response = self.get_fields(node + '/picture', 'url', 
                                              params=params)

        return response['url']

    def get_user_groups(self, node='me', 
                        fields=['id', 'name', 'privacy', 'description']):
        """
        Retrieve some information about the groups joined
        by the user whose id is given by the node parameter.

        note:   (1) since graph version 2.4 this does not 
                    work anymore and the result will be empty.

                (2) becareful, this will most probably work just
                    for the current user whose token is used.
        """

        #### fake response
        # return [
        #     { 'id':'0000000000', 'name':'group 0', 'privacy':'OPEN', 'description':'group 0' },
        #     { 'id':'1111111111', 'name':'group 1', 'privacy':'CLOSED', 'description':'group 1' },
        #     { 'id':'2222222222', 'name':'group 2', 'privacy':'OPEN', 'description':'group 2' },
        #     { 'id':'3333333333', 'name':'group 3', 'privacy':'OPEN', 'description':'group 3' },
        #     { 'id':'4444444444', 'name':'group 4', 'privacy':'CLOSED', 'description':'group 4' },
        #     { 'id':'5555555555', 'name':'group 5', 'privacy':'OPEN', 'description':'group 5' },
        #     { 'id':'6666666666', 'name':'group 6', 'privacy':'CLOSED', 'description':'group 6' },
        #     { 'id':'7777777777', 'name':'group 7', 'privacy':'OPEN', 'description':'group 7' },
        # ]

        return self.get_fields(node + '/groups', fields, 
                               version='2.3')

    def get_user_pages(self, node='me', 
                       fields=['id', 'name', 'about', 'access_token']):
        """
        Retrieve information about the pages managed by
        the user whose id is given by the node parameter.

        note:   (1) becareful, this will most probably work just
                    for the current user whose token is used.
        """

        #### fake response
        # return [
        #     { 'id':'0000000000', 'name':'page 0', 'about':'page 0', 'access_token':'DAfa2eaf5e423asdf2q2r@#Rafasdf@4adsfadfASaTet' },
        #     { 'id':'1111111111', 'name':'page 1', 'about':'page 1', 'access_token':'DAfa2eaf5e423asdf2q2r@#Rafasdf@4adsfadfASaTet' },
        #     { 'id':'2222222222', 'name':'page 2', 'about':'page 2', 'access_token':'DAfa2eaf5e423asdf2q2r@#Rafasdf@4adsfadfASaTet' },
        #     { 'id':'3333333333', 'name':'page 3', 'about':'page 3', 'access_token':'DAfa2eaf5e423asdf2q2r@#Rafasdf@4adsfadfASaTet' },
        # ]

        return self.get_fields(node + '/accounts', fields=fields)

    def get_token_permissions(self, node='me'):
        """
        Retrieve a list of permissions and their status whether
        granted or disallowed for the current token.

        note:   (1) becareful, this will work just for 
                    the current user whose token is used.
        """

        return self.get_fields(node + '/permissions', 
                               ['permission', 'status'])

    def get_token_granted_permissions(self):
        """
        Retrieve the list of granted permissions.
        """

        permissions = self.get_token_permissions()

        result = [permission['permission'] for permission 
                                           in permissions 
                    if permission['status'] == 'granted']
        
        return result

    def get_user_photos(self, node='me', type='uploaded', fields='id'):
        """
        Retrieve information about user photos whose id is given
        by the node parameter.

        parameters
            type        type of photos.
                        possible values: uploaded, tagged
        """

        return self.get_fields(node + '/photos', 
                               fields, 
                               params=dict(type=type))

    def get_user_feed(self, node='me', fields='id'):
        """
        Retrieve the feed for the user whose id is given
        by the node parameter.
        """

        return self.get_fields(node + '/feed', fields)

    def get_user_likes(self, node='me', 
                       fields=['id', 'name', 'about', 'can_post']):
        """
        Retrieve information about liked pages by the user whose 
        id is given by the node parameter.
        """

        #### fake response
        # return [
        #     { 'id':'0000000000', 'name':'liked page 0', 'about':'liked page 0', 'can_post':True },
        #     { 'id':'1111111111', 'name':'liked page 1', 'about':'liked page 1', 'can_post':False },
        #     { 'id':'2222222222', 'name':'liked page 2', 'about':'liked page 2', 'can_post':True },
        #     { 'id':'3333333333', 'name':'liked page 3', 'about':'liked page 3', 'can_post':False },
        # ]

        return self.get_fields(node + '/likes', fields)

    def put(self, node, 
                  params=None, 
                  post_args=None, 
                  files=None, 
                  version=None):
        """
        parameters

            node        :   The id of a Graph object supporting publishing.
            params      :   A dict() object to be sent in the query string for
                            the request.
            post_args   :   A dict() object to send in the body of the request.
            files       :   A dict() object of file-like objects for multipart
                            encoding upload.
                            [see: python requests documentation for reference.]
            version     :   The Graph version to be used.

        return
            id          :   The ID of the newly created Graph object.
        """

        if params is None:
            params = dict()

        if post_args is None:
            post_args = dict()

        if post_args.has_key('privacy'):
            privacy = dict(value=post_args['privacy'])
            post_args['privacy'] = json.dumps(privacy)

        if 'access_token' not in post_args:
            post_args['access_token'] = self.access_token

        if version is None:
            version = self.version

        version = 'v' + version

        url = FB_GRAPH_URL.format(version=version,
                                  node=node)

        try:
            response = self.session.post(url, 
                                        params=params, 
                                        data=post_args, 
                                        files=files)

        except requests.ConnectionError:

            raise FBGraphError(
                "Failed to establish a connection "
                "to the host.")

        except requests.RequestException as e:
            raise FBGraphError(e)

        result = response.json()

        if result.has_key('id'):
            return result['id']

        elif result.has_key('success'):
            return result['success']
        
        else:
            raise FBGraphError(result)

    def put_post(self, node, **args):
        """
        parameters

            node : A user, group or page id
            args :
                message     :   The main body of the post, otherwise 
                                called the status message.
                link        :   The URL of a link to attach to the post.
                picture     :   Determines the preview image associated 
                                with the link.
                name        :   Overwrites the title of the link preview.
                caption     :   Overwrites the caption under the title 
                                in the link preview.
                description :   Overwrites the description in the link preview
                place       :   Page ID of a location associated with this post.
                tags        :   Comma-separated list of user IDs of people 
                                tagged in this post. 
                                
                                Note: You cannot specify this field without 
                                      also specifying a place.
                privacy     :   Determines the privacy settings of the post. 
                                If not supplied, this defaults to the privacy 
                                level granted to the app in the Login Dialog. 
                                This field cannot be used to set a more open 
                                privacy setting than the one granted.
                    value   :   The value of the privacy setting.
                                enum {   
                                    'EVERYONE', 
                                    'ALL_FRIENDS', 
                                    'FRIENDS_OF_FRIENDS', 
                                    'CUSTOM', 
                                    'SELF'
                                }
                    allow   :   When value is CUSTOM, this is a comma-separated list 
                                of user IDs and friend list IDs that can see the post. 
                                This can also be ALL_FRIENDS or FRIENDS_OF_FRIENDS 
                                to include all members of those sets.
                    deny    :   When value is CUSTOM, this is a comma-separated list 
                                of user IDs and friend list IDs that cannot see the post.

                object_attachment   :   Facebook ID for an existing picture in the person's 
                                        photo albums to use as the thumbnail image. 
                                        They must be the owner of the photo, and the photo 
                                        cannot be part of a message attachment.

            Note: Either link, place, or message must be supplied.

        return

            id              :   The newly created post ID.
        """

        version = args.pop('version', None)

        return self.put(node + '/feed', 
                        post_args=args, 
                        version=version)

    def put_message(self, node, message, **args):
        """
        Publish a text post to the given node feed.
        """
        
        args['message'] = message

        ## fake publish
        # print 'post target :', node
        # print 'post message :', message
        # print 'arguments :', args
        # return True

        return self.put_post(node, **args)

    def put_link(self, node, link, **args):
        """
        Publish a link post to the given node feed.
        """

        args['link'] = link

        ## fake publish
        # print 'post target :', node
        # print 'post link :', link
        # print 'arguments :', args
        # return True
        
        return self.put_post(node, **args)

    def put_image(self, node, image, **args):
        """
        Upload a picture file to user photos.

        parameters
            
            image

            published
            
            args
                
                message
                
                caption
                
                privacy

        return
            
            The uploaded picture file ID.
        """

        files = dict()
        
        if os.path.isfile(image):
            files['source'] = open(image, 'rb')

        else:
            args['url'] = image

        version = args.pop('version', None)

        ## fake publish
        # print 'post target :', node
        # print 'post image :', image
        # print 'arguments :', args
        # return True

        return self.put(node + '/photos', 
                        post_args=args, 
                        files=files, 
                        version=version)

    def put_comment(self, node, **args):
        """
        parameters

            node    :   The id of an object supporting comments publishing.
            
            args    :
                message         :   The comment text.
                
                attachment_id   :   An optional ID of a unpublished photo uploaded 
                                    to Facebook to include as a photo comment. 
                
                attachment_url  :   The URL of an image to include as a photo comment.
                
                source          :   A photo, encoded as form data, to use as a photo comment.

                version         :   Graph API version to be used (passed to put()).

                Note:   One of attachment_url, attachment_id, message 
                        or source must be provided when publishing.

        return
                
                id                  :   The newly created comment ID.
        """

        version = args.pop('version', None)

        return self.put(node + '/comments', 
                        post_args=args, 
                        version=version)

    def delete(self, node, params=None, version=None):
        """
        Delete the graph node given by the node parameter.
        """

        if params is None:
            params = dict()
        
        if 'access_token' not in params:
            params['access_token'] = self.access_token
        
        params['format'] = 'json'

        if version is None:
            version = self.version

        version = 'v' + version

        url = FB_GRAPH_URL.format(version=version, 
                                  node=node)

        try:
            response = self.session.delete(url, params=params)

        except requests.ConnectionError:

            raise FBGraphError(
                "Failed to establish a connection "
                "to the host.")

        except requests.RequestException as e:
            
            raise FBGraphError(e)

        result = response.json()

        if result.has_key('success'):
            
            return True
        
        else:
            raise FBGraphError(result)

