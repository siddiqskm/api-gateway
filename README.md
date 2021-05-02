## Purpose
A standalone HTTP server that operates as a gateway for redirecting network traffic to the appropriate backend services (hosted on docker)

### Assumptions
- Only one port is mapped/exposed per backend service (as defined in docker-compose.yml)
- Docker containers are running before rgate is started
- What happens in case no backends are running - A response with status code 503 and message - Backend available but no Service URLs discovered is returned

### Design Choices
- Python is used for the development of this application
- Flask is used for all the web server related scenarios
- Sqlite is used as DB for storing the persistent data
- Pydantic is used for managing/handling the data vs requests vs responses
- Docker SDK for python is used for all the interactions with docker service

### Limitations/Enhancements (due to time/other constraints)
- Enhancments in code layout/structure/data structures/logging/python3 datatype annotations for method definitions etc can be implemented
- Instead of directly querying DB using a specific client, using an ORM (like sqlalchemy) for all the DB related operations could have been a better choice
- Auto refresh of backend services from rgate is not supported - i.e.
 - rgate discovers the backends available @ its startup
 - In case any of the backend services are started while rgate is running - they are not discovered

### Installation
- Male sure docker / sqlite3 / docker-compose / python3 / virtualenv are installed and available on the host machine, listed below are a few references in case required -
	- **brew install sqlite3** can be used for sqlite3 installation on MacOS
	- https://www.sqlitetutorial.net/download-install-sqlite/ - Installation instructions for other operating systems
	- https://docs.docker.com/desktop/#download-and-install - for docker
	- https://docs.docker.com/compose/install/ - for docker-compose
	- https://www.python.org/downloads/ - Make sure python is installed and ready to be use
	- https://pypi.org/project/virtualenv/ - Make sure virtualenv is installed and available on the host machine
- Create a virtual environment using the following command -
`virtualenv -p python3 ~/Desktop/venvs/rgate`
- Activate virtual environment -
`source ~/Desktop/venvs/rgate/bin/activate`
- Change working directory to root of rgate to make sure requirements.txt is listed
- Install rgate dependencies -
`pip install -r requirements.txt`
- Bring up the backend services (payment / orders) to make sure they are up and running, Build using (docker-compose build) if required -
`docker-compose up -d` - Generally takes care of build as well
- Start the rgate gateway with the following command -
`python rgate.py --port 8080 --config config.yml`

### Testing
- 2 backend containers namely payment and orders are available for testing
- A container is selected as a backend if the container has all the match_labels present as Docker labels. If there are multiple containers matching, a random container is selected as a backend
- Incoming http requests are routed to the corresponding backend if the path starts with the given path_prefix
- The responses from the backend services are returned in a consistent format
- If there are no routes matching the request, the server responds with the given body and status_code in the default_response
- If the backend is down, the server responds with a 503 code
- Accessing http://localhost:8080/stats gives the information about the traffic it
has received so far
- In case Backend services go down and are brought up momentarily - The connections from rgate to backend services are restored appropriately
- Other Misc related
