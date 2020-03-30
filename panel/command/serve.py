"""
Subclasses the bokeh serve commandline handler to extend it in various
ways.
"""

from glob import glob

from bokeh.command.subcommands.serve import Serve as _BkServe
from tornado.wsgi import WSGIContainer
from tornado.web import FallbackHandler

from ..io.server import INDEX_HTML
from ..util import bokeh_version


class Serve(_BkServe):

    args = _BkServe.args + (
        ('--rest-provider', dict(
            action = 'store',
            type   = str,
            help   = "The interface to use to serve REST API"
        )),
        ('--rest-endpoint', dict(
            action  = 'store',
            type    = str,
            help    = "Endpoint to store REST API on.",
            default = 'rest'
        ))
    )
    
    
    def customize_kwargs(self, args, server_kwargs):
        '''Allows subclasses to customize ``server_kwargs``.

        Should modify and return a copy of the ``server_kwargs`` dictionary.
        '''
        kwargs = dict(server_kwargs)
        if 'index' not in kwargs:
            kwargs['index'] = INDEX_HTML

        files = []
        for f in args.files:
            if args.glob:
                files.extend(glob(f))
            else:
                files.append(f)

        # Handle tranquilized functions in the supplied functions
        kwargs['extra_patterns'] = patterns = []
        if args.rest_provider == 'tranquilizer':
            from ..io.rest import build_tranquilize_application
            app = build_tranquilize_application(files, args)
            tr = WSGIContainer(app)
            patterns.append((r"^/%s/.*" % args.rest_endpoint, FallbackHandler, dict(fallback=tr)))
        elif args.rest_provider is not None:
            raise ValueError("rest-provider %r not recognized." % args.rest_provider)
        return server_kwargs

    def invoke(self, args):
        if bokeh_version < '2.0.1' and args.rest_provider:
            raise ValueError("Serving REST endpoints requires Bokeh>=2.0.1.")
        super(Serve, self).invoke(args)
