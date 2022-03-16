#!../venv/bin/python
# from app import webapp
# from app.main import main

# from werkzeug.serving import run_simple  # werkzeug development server
# use to combine each Flask app into a larger one that is dispatched based on prefix
# from werkzeug.middleware.dispatcher import DispatcherMiddleware


from backEnd import webapp as backEnd

backEnd.secret_key = "Secreeeeeeeeeeet"


# application = DispatcherMiddleware({'/backEnd': backEnd})

if __name__ == "__main__":

    backEnd.run(host='0.0.0.0', port=5001)
    # """Using "threaded = True", the function can call API within itself while dealing with user requests.
    # """
    # run_simple('0.0.0.0', 5001, application,
    #            use_reloader=True,
    #            use_debugger=True,
    #            use_evalex=True,
    #            threaded=True)
