# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2019 Tom Kralidis
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

import json
import os

import pytest

from werkzeug.test import create_environ
from werkzeug.wrappers import Request
from pygeoapi.api import API, check_format
from pygeoapi.util import yaml_load


def get_test_file_path(filename):
    """helper function to open test file safely"""

    if os.path.isfile(filename):
        return filename
    else:
        return 'tests/{}'.format(filename)


def make_req_headers(**kwargs):
    environ = create_environ('/collections/obs/items',
                             'http://localhost:5000/')
    environ.update(kwargs)
    request = Request(environ)
    return request.headers


@pytest.fixture()
def config():
    with open(get_test_file_path('pygeoapi-test-config.yml')) as fh:
        return yaml_load(fh)


@pytest.fixture()
def openapi():
    with open(get_test_file_path('pygeoapi-test-openapi.yml')) as fh:
        return yaml_load(fh)


@pytest.fixture()
def api_(config):
    return API(config)


def test_api(config, api_, openapi):
    assert api_.config == config
    assert isinstance(api_.config, dict)

    req_headers = make_req_headers(HTTP_CONTENT_TYPE='application/json')
    rsp_headers, code, response = api_.api(req_headers, {}, openapi)
    assert rsp_headers['Content-Type'] ==\
        'application/vnd.oai.openapi+json;version=3.0'
    root = json.loads(response)

    assert isinstance(root, dict)

    a = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    req_headers = make_req_headers(HTTP_ACCEPT=a)
    rsp_headers, code, response = api_.api(req_headers, {}, openapi)
    assert rsp_headers['Content-Type'] == 'text/html'

    req_headers = make_req_headers()
    rsp_headers, code, response = api_.api(req_headers, {'f': 'foo'}, openapi)
    assert code == 400


def test_api_exception(config, api_):
    req_headers = make_req_headers()
    rsp_headers, code, response = api_.root(req_headers, {'f': 'foo'})
    assert code == 400


def test_root(config, api_):
    req_headers = make_req_headers()
    rsp_headers, code, response = api_.root(req_headers, {})
    root = json.loads(response)

    assert rsp_headers['Content-Type'] == 'application/json'
    assert rsp_headers['X-Powered-By'].startswith('pygeoapi')

    assert isinstance(root, dict)
    assert 'links' in root
    assert len(root['links']) == 6
    assert 'title' in root
    assert root['title'] == 'pygeoapi default instance'
    assert 'description' in root
    assert root['description'] == 'pygeoapi provides an API to geospatial data'

    rsp_headers, code, response = api_.root(req_headers, {'f': 'html'})
    assert rsp_headers['Content-Type'] == 'text/html'


def test_api_conformance(config, api_):
    req_headers = make_req_headers()
    rsp_headers, code, response = api_.api_conformance(req_headers, {})
    root = json.loads(response)

    assert isinstance(root, dict)
    assert 'conformsTo' in root
    assert len(root['conformsTo']) == 4

    rsp_headers, code, response = api_.api_conformance(
        req_headers, {'f': 'foo'})
    assert code == 400

    rsp_headers, code, response = api_.api_conformance(
        req_headers, {'f': 'html'})
    assert rsp_headers['Content-Type'] == 'text/html'


def test_describe_collections(config, api_):
    req_headers = make_req_headers()
    rsp_headers, code, response = api_.describe_collections(
        req_headers, {'f': 'foo'})
    assert code == 400

    req_headers = make_req_headers()
    rsp_headers, code, response = api_.describe_collections(
        req_headers, {'f': 'html'})
    assert rsp_headers['Content-Type'] == 'text/html'

    rsp_headers, code, response = api_.describe_collections(
        req_headers, {})
    collections = json.loads(response)

    assert len(collections) == 2
    assert len(collections['collections']) == 1
    assert len(collections['links']) == 2

    rsp_headers, code, response = api_.describe_collections(
        req_headers, {}, 'foo')
    collection = json.loads(response)

    assert code == 400

    rsp_headers, code, response = api_.describe_collections(
        req_headers, {}, 'obs')
    collection = json.loads(response)

    assert collection['id'] == 'obs'
    assert collection['title'] == 'Observations'
    assert collection['description'] == 'My cool observations'
    assert len(collection['links']) == 6
    assert collection['extent'] == {
        'spatial': {
            'bbox': [[-180, -90, 180, 90]],
            'crs': 'http://www.opengis.net/def/crs/OGC/1.3/CRS84'
        },
        'temporal': {
            'interval': [['2000-10-30T18:24:39', '2007-10-30T08:57:29']],
            'trs': 'http://www.opengis.net/def/uom/ISO-8601/0/Gregorian'
        }
    }

    rsp_headers, code, response = api_.describe_collections(
        req_headers, {'f': 'html'}, 'obs')
    assert rsp_headers['Content-Type'] == 'text/html'


def test_get_features(config, api_):
    req_headers = make_req_headers()
    rsp_headers, code, response = api_.get_features(
        req_headers, {}, 'foo')
    features = json.loads(response)

    assert code == 400

    rsp_headers, code, response = api_.get_features(
        req_headers, {'f': 'foo'}, 'obs')
    features = json.loads(response)

    assert code == 400

    rsp_headers, code, response = api_.get_features(
        req_headers, {'bbox': '1,2,3'}, 'obs')
    features = json.loads(response)

    assert code == 400

    rsp_headers, code, response = api_.get_features(
        req_headers, {'bbox': '1,2,3,4c'}, 'obs')

    assert code == 400

    rsp_headers, code, response = api_.get_features(
        req_headers, {'f': 'html'}, 'obs')
    assert rsp_headers['Content-Type'] == 'text/html'

    rsp_headers, code, response = api_.get_features(req_headers, {}, 'obs')
    features = json.loads(response)

    assert len(features['features']) == 5

    rsp_headers, code, response = api_.get_features(
        req_headers, {'resulttype': 'hits'}, 'obs')
    features = json.loads(response)

    assert len(features['features']) == 0

    # Invalid limit
    rsp_headers, code, response = api_.get_features(
        req_headers, {'limit': 0}, 'obs')
    features = json.loads(response)

    assert code == 400

    rsp_headers, code, response = api_.get_features(
        req_headers, {'limit': 2}, 'obs')
    features = json.loads(response)

    assert len(features['features']) == 2
    assert features['features'][1]['properties']['stn_id'] == '35'

    links = features['links']
    assert len(links) == 4
    assert '/collections/obs/items?f=json' in links[0]['href']
    assert links[0]['rel'] == 'self'
    assert '/collections/obs/items?f=html' in links[1]['href']
    assert links[1]['rel'] == 'alternate'
    assert '/collections/obs/items?startindex=2&limit=2' in links[2]['href']
    assert links[2]['rel'] == 'next'
    assert '/collections/obs' in links[3]['href']
    assert links[3]['rel'] == 'collection'

    # Invalid startindex
    rsp_headers, code, response = api_.get_features(
        req_headers, {'startindex': -1}, 'obs')
    features = json.loads(response)

    assert code == 400

    rsp_headers, code, response = api_.get_features(
        req_headers, {'startindex': 2}, 'obs')
    features = json.loads(response)

    assert len(features['features']) == 3
    assert features['features'][1]['properties']['stn_id'] == '2147'

    links = features['links']
    assert len(links) == 4
    assert '/collections/obs/items?f=json' in links[0]['href']
    assert links[0]['rel'] == 'self'
    assert '/collections/obs/items?f=html' in links[1]['href']
    assert links[1]['rel'] == 'alternate'
    assert '/collections/obs/items?startindex=0' in links[2]['href']
    assert links[2]['rel'] == 'prev'
    assert '/collections/obs' in links[3]['href']
    assert links[3]['rel'] == 'collection'

    rsp_headers, code, response = api_.get_features(
        req_headers, {'startindex': 1, 'limit': 1,
                      'bbox': '-180,90,180,90'}, 'obs')
    features = json.loads(response)

    assert len(features['features']) == 1

    links = features['links']
    assert len(links) == 5
    assert '/collections/obs/items?f=json&limit=1&bbox=-180,90,180,90' in \
        links[0]['href']
    assert links[0]['rel'] == 'self'
    assert '/collections/obs/items?f=html&limit=1&bbox=-180,90,180,90' in \
        links[1]['href']
    assert links[1]['rel'] == 'alternate'
    assert '/collections/obs/items?startindex=0&limit=1&bbox=-180,90,180,90' \
        in links[2]['href']
    assert links[2]['rel'] == 'prev'
    assert '/collections/obs/items?startindex=2&limit=1&bbox=-180,90,180,90' \
        in links[3]['href']
    assert links[3]['rel'] == 'next'
    assert '/collections/obs' in links[4]['href']
    assert links[4]['rel'] == 'collection'

    rsp_headers, code, response = api_.get_features(
        req_headers, {'sortby': 'stn_id', 'stn_id': '35'}, 'obs')

    assert code == 400

    rsp_headers, code, response = api_.get_features(
        req_headers, {'sortby': 'stn_id:FOO', 'stn_id': '35', 'value': '89.9'},
        'obs')

    assert code == 400

    rsp_headers, code, response = api_.get_features(
        req_headers, {'sortby': 'stn_id:A'}, 'obs')
    features = json.loads(response)
    # FIXME? this test errors out currently
    assert code == 400

    rsp_headers, code, response = api_.get_features(
        req_headers, {'f': 'csv'}, 'obs')

    assert rsp_headers['Content-Type'] == 'text/csv; charset=utf-8'

    rsp_headers, code, response = api_.get_features(
        req_headers, {'datetime': '2003'}, 'obs')

    assert code == 200

    rsp_headers, code, response = api_.get_features(
        req_headers, {'datetime': '1999'}, 'obs')

    assert code == 400

    rsp_headers, code, response = api_.get_features(
        req_headers, {'datetime': '2010-04-22'}, 'obs')

    assert code == 400

    rsp_headers, code, response = api_.get_features(
        req_headers, {'datetime': '2001-11-11/2003-12-18'}, 'obs')

    assert code == 200

    rsp_headers, code, response = api_.get_features(
        req_headers, {'datetime': '../2003-12-18'}, 'obs')

    assert code == 200

    rsp_headers, code, response = api_.get_features(
        req_headers, {'datetime': '2001-11-11/..'}, 'obs')

    assert code == 200

    rsp_headers, code, response = api_.get_features(
        req_headers, {'datetime': '1999/2005-04-22'}, 'obs')

    assert code == 400

    rsp_headers, code, response = api_.get_features(
        req_headers, {'datetime': '2002/2014-04-22'}, 'obs')

    api_.config['datasets']['obs']['extents'].pop('temporal')

    rsp_headers, code, response = api_.get_features(
        req_headers, {'datetime': '2002/2014-04-22'}, 'obs')

    assert code == 200


def test_get_feature(config, api_):
    req_headers = make_req_headers()
    rsp_headers, code, response = api_.get_feature(
        req_headers, {'f': 'foo'}, 'obs', '371')

    assert code == 400

    rsp_headers, code, response = api_.get_feature(
        req_headers, {}, 'foo', '371')

    assert code == 400

    rsp_headers, code, response = api_.get_feature(
        req_headers, {}, 'obs', 'notfound')

    assert code == 404

    rsp_headers, code, response = api_.get_feature(
        req_headers, {'f': 'html'}, 'obs', '371')

    assert rsp_headers['Content-Type'] == 'text/html'

    rsp_headers, code, response = api_.get_feature(
        req_headers, {}, 'obs', '371')
    features = json.loads(response)

    assert features['properties']['stn_id'] == '35'


def test_describe_processes(config, api_):
    req_headers = make_req_headers()

    # Test for undefined process
    rsp_headers, code, response = api_.describe_processes(
        req_headers, {}, 'foo')
    data = json.loads(response)
    assert code == 404
    assert data['code'] == 'NoSuchProcess'

    # Test for description of all processes
    rsp_headers, code, response = api_.describe_processes(
        req_headers, {})
    data = json.loads(response)
    assert code == 200
    assert len(data['processes']) == 1

    # Test for particular, defined procss
    rsp_headers, code, response = api_.describe_processes(
        req_headers, {}, 'hello-world')
    process = json.loads(response)
    assert code == 200
    assert rsp_headers['Content-Type'] == 'application/json'
    assert process['id'] == 'hello-world'
    assert process['version'] == '0.2.0'
    assert process['title'] == 'Hello World process'
    assert len(process['keywords']) == 3
    assert len(process['links']) == 2
    assert len(process['inputs']) == 2
    assert len(process['outputs']) == 1
    assert len(process['outputTransmission']) == 1
    assert len(process['jobControlOptions']) == 1
    assert process['jobControlOptions'][0] == 'sync-execute'

    # Check HTML response when requested in headers
    req_headers = make_req_headers(HTTP_ACCEPT='text/html')
    rsp_headers, code, response = api_.describe_processes(
        req_headers, {}, 'hello-world')
    assert code == 200
    assert rsp_headers['Content-Type'] == 'text/html'

    # Check JSON response when requested in headers
    req_headers = make_req_headers(HTTP_ACCEPT='application/json')
    rsp_headers, code, response = api_.describe_processes(
        req_headers, {}, 'hello-world')
    assert code == 200
    assert rsp_headers['Content-Type'] == 'application/json'

    # Check HTML response when requested with query parameter
    req_headers = make_req_headers()
    rsp_headers, code, response = api_.describe_processes(
        req_headers, {'f': 'html'}, 'hello-world')
    assert code == 200
    assert rsp_headers['Content-Type'] == 'text/html'

    # Check JSON response when requested with query parameter
    req_headers = make_req_headers()
    rsp_headers, code, response = api_.describe_processes(
        req_headers, {'f': 'json'}, 'hello-world')
    assert code == 200
    assert rsp_headers['Content-Type'] == 'application/json'

    # Reset config to have no defined processes
    api_.config['processes'] = {}

    # Test for undefined process
    req_headers = make_req_headers()
    rsp_headers, code, response = api_.describe_processes(
        req_headers, {}, 'foo')
    data = json.loads(response)
    assert code == 404
    assert data['code'] == 'NoSuchProcess'
    assert rsp_headers['Content-Type'] == 'application/json'

    # Test for description of all processes
    rsp_headers, code, response = api_.describe_processes(
        req_headers, {})
    data = json.loads(response)
    assert code == 200
    assert len(data['processes']) == 0
    assert rsp_headers['Content-Type'] == 'application/json'

    # Reset config to have no mention of processes at all
    api_.config.pop('processes')

    # Test for undefined process
    req_headers = make_req_headers()
    rsp_headers, code, response = api_.describe_processes(
        req_headers, {}, 'foo')
    data = json.loads(response)
    assert code == 404
    assert data['code'] == 'NoSuchProcess'
    assert rsp_headers['Content-Type'] == 'application/json'

    # Test for description of all processes
    rsp_headers, code, response = api_.describe_processes(
        req_headers, {})
    data = json.loads(response)
    assert code == 200
    assert len(data['processes']) == 0
    assert rsp_headers['Content-Type'] == 'application/json'


def test_execute_process(config, api_):
    req_headers = make_req_headers()
    req_body = {
        'inputs': [{
            'id': 'name',
            'value': 'Test'
        }]
    }
    req_body_2 = {
        'inputs': [{
            'id': 'name',
            'value': 'Tést'
        }]
    }
    req_body_3 = {
        'inputs': [{
            'id': 'name',
            'value': 'Tést'
        }, {
            'id': 'message',
            'value': 'This is a test.'
        }]
    }
    req_body_4 = {
        'inputs': [{
            'id': 'foo',
            'value': 'Tést'
        }]
    }

    # Test posting empty payload to existing process
    rsp_headers, code, response = api_.execute_process(
        'POST', req_headers, {}, '', 'hello-world')
    data = json.loads(response)
    assert code == 400
    assert 'Location' not in rsp_headers
    assert data['code'] == 'MissingParameterValue'

    rsp_headers, code, response = api_.execute_process(
        'POST', req_headers, {}, json.dumps(req_body), 'foo')
    data = json.loads(response)
    assert code == 404
    assert 'Location' not in rsp_headers
    assert data['code'] == 'NoSuchProcess'

    rsp_headers, code, response = api_.execute_process(
        'POST', req_headers, {}, json.dumps(req_body), 'hello-world')
    data = json.loads(response)
    assert code == 201
    assert 'Location' in rsp_headers
    assert len(data['outputs']) == 1
    assert data['outputs'][0]['id'] == 'echo'
    assert data['outputs'][0]['value'] == 'Hello Test!'

    rsp_headers, code, response = api_.execute_process(
        'POST', req_headers, {}, json.dumps(req_body_2), 'hello-world')
    data = json.loads(response)
    assert code == 201
    assert 'Location' in rsp_headers
    assert data['outputs'][0]['value'] == 'Hello Tést!'

    rsp_headers, code, response = api_.execute_process(
        'POST', req_headers, {}, json.dumps(req_body_3), 'hello-world')
    data = json.loads(response)
    assert code == 201
    assert 'Location' in rsp_headers
    assert data['outputs'][0]['value'] == 'Hello Tést! This is a test.'

    rsp_headers, code, response = api_.execute_process(
        'POST', req_headers, {}, json.dumps(req_body_4), 'hello-world')
    data = json.loads(response)
    assert code == 201
    assert 'Location' in rsp_headers
    assert data['code'] == 'InvalidParameterValue'
    # TODO inspect Location URI and asset 400 status

    # Reset config to have no defined processes
    api_.config['processes'] = {}

    req_headers = make_req_headers()
    rsp_headers, code, response = api_.execute_process(
        'POST', req_headers, {}, json.dumps(req_body), 'hello-world')
    response = json.loads(response)
    assert code == 404
    assert 'Location' not in rsp_headers
    assert response['code'] == 'NoSuchProcess'

    # Reset config to have no mention of processes at all
    api_.config.pop('processes')

    req_headers = make_req_headers()
    rsp_headers, code, response = api_.execute_process(
        'POST', req_headers, {}, json.dumps(req_body), 'hello-world')
    response = json.loads(response)
    assert code == 404
    assert 'Location' not in rsp_headers
    assert response['code'] == 'NoSuchProcess'


def test_check_format():
    args = {
        'f': 'html'
    }

    req_headers = {}

    assert check_format({}, req_headers) is None

    assert check_format(args, req_headers) == 'html'

    args['f'] = 'json'
    assert check_format(args, req_headers) == 'json'

    args['f'] = 'html'
    assert check_format(args, req_headers) == 'html'

    req_headers['Accept'] = 'text/html'
    assert check_format({}, req_headers) == 'html'

    req_headers['Accept'] = 'application/json'
    assert check_format({}, req_headers) == 'json'

    req_headers['accept'] = 'text/html'
    assert check_format({}, req_headers) == 'html'

    hh = 'text/html,application/xhtml+xml,application/xml;q=0.9,'

    req_headers['Accept'] = hh
    assert check_format({}, req_headers) == 'html'

    req_headers['accept'] = hh
    assert check_format({}, req_headers) == 'html'

    req_headers = make_req_headers(HTTP_ACCEPT=hh)
    assert check_format({}, req_headers) == 'html'

    req_headers = make_req_headers(HTTP_ACCEPT='text/html')
    assert check_format({}, req_headers) == 'html'

    req_headers = make_req_headers(HTTP_ACCEPT='application/json')
    assert check_format({}, req_headers) == 'json'

    # Overrule HTTP content negotiation
    args['f'] = 'html'
    assert check_format(args, req_headers) == 'html'

    req_headers = make_req_headers(HTTP_ACCEPT='text/html')
    args['f'] = 'json'
    assert check_format(args, req_headers) == 'json'
