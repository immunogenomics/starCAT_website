from minimal import create_app
import os

if __name__ == "__main__":
	app = create_app()
	app.run(port=8001)
