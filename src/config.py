def load_config(source = None):
    if source is None:
        source = '../config.yaml'
    import yaml
    globs = globals()
    def abort(message):
        import sys
        print >>sys.stderr, "Bad configuration: {0}".format(message)
        sys.exit(1)
    try:
        with open(source, 'r') as f:
            configuration = yaml.load(f)
            if not isinstance(configuration, dict):
                abort("Config file root node is not a dictionary?")
            globs.update(configuration)
            del globs['load_config']
    except IOError:
        abort("No config.yaml found")

