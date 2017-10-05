from dataimporter.factory import create_app

app = create_app(blueprints=True)

if not app.debug:
    import logging
    from logging import Formatter

    file_handler = logging.FileHandler('./dataimporter.log')
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))

    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.DEBUG)
