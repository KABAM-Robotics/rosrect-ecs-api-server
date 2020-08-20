from sanic import Sanic, response
from sanic.response import json, html, text
from databases import Database
import os

app = Sanic(__name__)

app.static('/static', './static')

app.url_for('static', filename='favicon.ico') == '/static/favicon.ico'

# Parsing API Components 
ecs_api_url = os.environ['ECS_API']
ecs_api_url = ecs_api_url.replace('/','')
api_comp = ecs_api_url.split(':')
api_host = api_comp[1]
api_port = api_comp[2]

@app.route("/")
async def main_index(request):
    template = open("index.html")
    return html(template.read())


@app.route("/api/ert/getAllData")
async def get_ert_alldata(request):
    """ Test API that can be used to quickly see ERT data """

    # Get database
    db = request.app.config['database']

    # Set query
    query = """
            SELECT error_code, robot_model, error_source, error_text
            FROM error_report;
            """

    # Retrieve query
    rows = await db.fetch_all(query=query)

    # Return results
    return response.json({'status': 200, 'data': jsonify(rows)}, status=200)


@app.route("/api/ert/getErrorData")
async def get_ert_errordata(request):
    """ Primary API that can be used to retrieve ERT row corresponding to a robot model/error text combo 
        ERT should be primarily used only in development environment, not production. """

    # Get database
    db = request.app.config['database']

    # Get query parameters
    query_params = request.args
    RobotModel = query_params.get('RobotModel')
    ErrorText = query_params.get('ErrorText')

    # Set query
    query = """
            SELECT error_code, cast(error_level as integer) as 'error_level', compounding_flag, error_module, error_source, error_text, error_description, error_resolution
            FROM error_report
            WHERE (:robot_model LIKE robot_model COLLATE NOCASE) AND (:error_text LIKE error_text COLLATE NOCASE); 
            """

    # Retrieve query
    rows = await db.fetch_all(query=query, values={"robot_model": RobotModel, "error_text": ErrorText})
    
    # Return results
    return response.json({'status': 200, 'data': jsonify(rows)}, status=200)


@app.route("/api/ecs/getAllData")
async def get_ecs_alldata(request):
    """ Test API that can be used to quickly see ECS data """

    # Get database
    db = request.app.config['database']

    # Set query
    query = """
            SELECT client_error_code, cognicept_error_code, error_module, error_source, error_text
            FROM error_classification
            """

    # Retrieve query
    rows = await db.fetch_all(query=query)

    # Return results
    return response.json({'status': 200, 'data': jsonify(rows)}, status=200)


@app.route("/api/ecs/getErrorData")
async def get_ecs_errordata(request):
    """ Primary API that can be used to retrieve ECS row corresponding to a robot model/error text combo 
        ECS should be the primary choice in a production environment. """

    # Get database
    db = request.app.config['database']

    # Get query parameters
    query_params = request.args
    RobotModel = query_params.get('RobotModel')
    ErrorText = query_params.get('ErrorText')

    # Set query
    query = """
            SELECT X.cognicept_error_code, X.severity, X.compounding_flag, X.error_module, X.error_source, X.error_text
            FROM (error_classification EC
            INNER JOIN robot_info RI ON EC.robot_type = RI.robot_id) X
            WHERE :robot_model LIKE X.robot_model COLLATE NOCASE
            AND :error_text LIKE X.error_text COLLATE NOCASE
            """
    # Retrieve query
    rows = await db.fetch_all(query=query, values={"robot_model": RobotModel, "error_text": ErrorText})

    # Return results
    return response.json({'status': 200, 'data': jsonify(rows)}, status=200)


@app.listener('before_server_start')
async def register_db(app, loop):
    # Create a database connection
    db_path = os.path.expanduser(os.environ['ECS_DB_LOC'])
    app.config['database'] = Database(
        'sqlite:///'+ db_path)
    await app.config['database'].connect()


@app.listener('after_server_stop')
async def close_connection(app, loop):
    # Disconnect from database
    await app.config['database'].disconnect()


def jsonify(records):
    """
    Parse db record response into JSON format
    """
    raw_list = []
    for r in records:
        items = r.items()
        raw_list.append({i[0]: i[1].rstrip() if type(
            i[1]) == str else i[1] for i in items})

    # Process data for compounding flag to be boolean since SQLite does not have a boolean type
    processed_list = []
    for row in raw_list:
        if 'compounding_flag' in row:
            if row['compounding_flag'] == 'true':
                row['compounding_flag'] = True
            else:
                row['compounding_flag'] = False
            processed_list.append(row)
    
    # If processed list is empty, no processing was done, just assign raw list
    if not processed_list:
        processed_list = raw_list

    return processed_list


if __name__ == "__main__":

    try:
        app.run(port=api_port,
                access_log=True, debug=False)
    except Exception as e:
        print('Exception message: ', e)