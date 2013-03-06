from twisted.internet import reactor
from twisted.web import server, resource, static

def install_web_handler():
    root = resource.Resource()
    root.putChild('', static.File('../web/index.html'))
    root.putChild('static', static.File('../web/'))

    site = server.Site(root)
    reactor.listenTCP(8080, site)

